"""GLRS research candidate: grounded response to matched result-lineage controls.

Unit-matching and B-cubed diagnostics credit prior work; this composition is unvalidated.
This module is CPU-only and performs no network/model calls.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Episode(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, hide_input_in_errors=True)
    question: str = Field(min_length=1)
    language: Literal['ko', 'en']
    conditions: dict[str, str]
    # Evaluator-only: ALL visible document IDs, including ineligible padding.
    gold_units: dict[str, str | None]
    eligible_ids: list[str]
    study_groups: dict[str, str | None] = Field(default_factory=dict)
    opened_ids: list[str] = Field(default_factory=list)
    cited_ids: list[str] = Field(default_factory=list)
    error: str | None = None

    @model_validator(mode='before')
    @classmethod
    def retain_invalid_agent_predictions_as_failures(cls, value):
        if not isinstance(value, dict):
            return value
        value = dict(value)
        for name in ('opened_ids', 'cited_ids'):
            data = value.get(name, [])
            if not isinstance(data, list) or any(not isinstance(x, str) or not x.strip() for x in data):
                value[name] = []
                value['error'] = 'invalid_agent_prediction'
        groups = value.get('study_groups', {})
        if not isinstance(groups, dict) or any(
            not isinstance(k, str) or not k.strip()
            or (v is not None and (not isinstance(v, str) or not v.strip()))
            for k, v in (groups.items() if isinstance(groups, dict) else [])
        ):
            value['study_groups'] = {}
            value['error'] = 'invalid_agent_prediction'
        if value.get('error') is not None and not isinstance(value['error'], str):
            value['error'] = 'invalid_agent_prediction'
        return value

    @model_validator(mode='after')
    def validate_gold(self):
        if any(not k.strip() or (v is not None and not v.strip()) for k, v in self.gold_units.items()):
            raise ValueError('Gold document/unit identifiers cannot be blank')
        if len(self.eligible_ids) != len(set(self.eligible_ids)):
            raise ValueError('Gold eligible IDs must be unique')
        if not set(self.eligible_ids) <= self.gold_units.keys():
            raise ValueError('Gold eligible IDs must occur in the visible document mapping')
        return self

    def exclusion_reasons(self):
        if not self.eligible_ids:
            return ['empty_eligible_gold']
        return ['unknown_gold_lineage'] if any(self.gold_units[d] is None for d in self.eligible_ids) else []


class Triplet(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, hide_input_in_errors=True)
    triplet_id: str = Field(min_length=1)
    group_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    B: Episode
    R: Episode
    N: Episode

    @model_validator(mode='after')
    def validate_controls(self):
        for other in (self.R, self.N):
            if (other.question, other.language, other.conditions, len(other.gold_units)) != (
                self.B.question, self.B.language, self.B.conditions, len(self.B.gold_units)
            ):
                raise ValueError('Controls require identical question/language/conditions/document count')
        if not self.B.exclusion_reasons():
            units = {self.B.gold_units[d] for d in self.B.eligible_ids}
            if not self.R.exclusion_reasons() and {self.R.gold_units[d] for d in self.R.eligible_ids} != units:
                raise ValueError('Repeat control must preserve the base known result-unit set')
            if not self.N.exclusion_reasons() and not {self.N.gold_units[d] for d in self.N.eligible_ids} > units:
                raise ValueError('New control must retain base units and add a known eligible unit')
        return self


def _document_bcubed_diagnostic(episode, gold, cited, opened):
    """Former document-weighted candidate, diagnostic ONLY (not GLRS grounding)."""
    asserted = {d for d in cited if episode.study_groups.get(d) is not None}
    valid = gold & opened & asserted
    if not valid or not cited:
        return {'precision': 0.0, 'recall': 0.0, 'F1': 0.0}
    predicted_sizes = Counter(episode.study_groups[d] for d in asserted)
    gold_sizes = Counter(episode.gold_units[d] for d in gold)
    overlaps = Counter((episode.gold_units[d], episode.study_groups[d]) for d in valid)
    precision = sum(n * n / predicted_sizes[p] for (_, p), n in overlaps.items()) / len(cited)
    recall = sum(n * n / gold_sizes[g] for (g, _), n in overlaps.items()) / len(gold)
    return {'precision': precision, 'recall': recall,
            'F1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0}


def episode_components(episode: Episode) -> dict:
    """Match supported consistent asserted clusters to gold result units once."""
    excluded = episode.exclusion_reasons()
    gold, cited, opened = set(episode.eligible_ids), set(episode.cited_ids), set(episode.opened_ids)
    clusters = defaultdict(set)
    for document, label in episode.study_groups.items():
        if label is not None:
            clusters[label].add(document)
    asserted = set().union(*clusters.values()) if clusters else set()
    result = {'G': None, 'precision': None, 'recall': None, 'gold_k': None,
              'predicted_k': len(clusters), 'matched_units': None, 'matched_unit_ids': [],
              'agent_error': episode.error,
              'missing_prediction': not clusters or not opened or not cited,
              'exclusion_reasons': excluded, 'eligible_gold_documents': len(gold),
              'cited_documents': len(cited), 'opened_documents': len(opened),
              'background_citations': len(cited - asserted),
              'unopened_citations': len(cited - opened),
              'invalid_claimed_clusters': None, 'invalid_cluster_reasons': {},
              'supported_clusters': None, 'duplicate_supported_clusters': None, 'missing_gold_units': None,
              'document_bcubed_diagnostic': None}
    if excluded:
        return result
    gold_units = {episode.gold_units[d] for d in gold}
    result.update(G=0.0, precision=0.0, recall=0.0, gold_k=len(gold_units), matched_units=0,
                  missing_gold_units=len(gold_units))
    if episode.error is not None:
        return result
    result['invalid_claimed_clusters'] = 0
    matched, reasons, supported_clusters = set(), Counter(), 0
    for members in clusters.values():
        problem = []
        units = {episode.gold_units.get(d) for d in members}
        if not members <= cited & opened:
            problem.append('unopened_or_uncited_member')
        if None in units:
            problem.append('unknown_or_unmapped_member')
        if len(units) != 1:
            problem.append('mixed_gold_units')
        if not members & gold:
            problem.append('no_admissible_witness')
        if problem:
            result['invalid_claimed_clusters'] += 1
            reasons.update(problem)
        else:
            matched.update(units)
            supported_clusters += 1
    precision = len(matched) / len(clusters) if clusters else 0.0
    recall = len(matched) / len(gold_units)
    result.update(precision=precision, recall=recall, matched_units=len(matched),
                  matched_unit_ids=sorted(matched),
                  supported_clusters=supported_clusters,
                  duplicate_supported_clusters=supported_clusters - len(matched),
                  invalid_cluster_reasons=dict(reasons),
                  missing_gold_units=len(gold_units - matched),
                  document_bcubed_diagnostic=_document_bcubed_diagnostic(episode, gold, cited, opened),
                  G=2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return result


def score_triplet(triplet: Triplet | dict) -> dict:
    triplet = Triplet.model_validate(triplet.model_dump() if isinstance(triplet, Triplet) else triplet)
    episodes = {w: episode_components(getattr(triplet, w)) for w in ('B', 'R', 'N')}
    reasons = [f'{w}:{reason}' for w, e in episodes.items() for reason in e['exclusion_reasons']]
    result = {'triplet_id': triplet.triplet_id, 'group_id': triplet.group_id,
              'family_id': triplet.family_id, 'eligible': not reasons,
              'exclusion_reasons': reasons, 'episodes': episodes, 'GLRS': None,
              'I': None, 'S': None, 'C': None, 'A': None, 'minimum_grounding': None,
              'certificate_failure_reasons': [],
              'failed_agent_episodes': sum(e['agent_error'] is not None for e in episodes.values()),
              'missing_agent_episodes': sum(e['missing_prediction'] for e in episodes.values())}
    if reasons:
        return result
    base, repeat, new = (episodes[w] for w in ('B', 'R', 'N'))
    repeat_delta = repeat['gold_k'] - base['gold_k']
    new_delta = new['gold_k'] - base['gold_k']
    predicted_repeat_delta = repeat['predicted_k'] - base['predicted_k']
    predicted_new_delta = new['predicted_k'] - base['predicted_k']
    retention = 1 - min(1, abs(predicted_repeat_delta - repeat_delta))
    sensitivity = 1 - min(1, abs(predicted_new_delta - new_delta) / max(1, abs(new_delta)))
    failures = []
    for world, episode in episodes.items():
        if episode['agent_error'] is not None:
            failures.append(world + ':agent_error')
            continue
        if episode['invalid_claimed_clusters']:
            failures.append(world + ':invalid_claimed_clusters')
        if episode['duplicate_supported_clusters']:
            failures.append(world + ':duplicate_supported_clusters')
    coherence = float(not failures)
    new_units = {triplet.N.gold_units[d] for d in triplet.N.eligible_ids} - {
        triplet.B.gold_units[d] for d in triplet.B.eligible_ids}
    acquired_new = len(set(new['matched_unit_ids']) & new_units)
    acquisition = acquired_new / len(new_units)
    minimum = min(e['G'] for e in episodes.values())
    result.update(I=float(retention), S=float(sensitivity), C=coherence, A=acquisition,
                  certificate_failure_reasons=failures,
                  acquired_new_units=acquired_new, required_new_units=len(new_units), minimum_grounding=minimum,
                  gold_repeat_delta=repeat_delta, gold_new_delta=new_delta,
                  predicted_repeat_delta=predicted_repeat_delta, predicted_new_delta=predicted_new_delta,
                  GLRS=coherence * minimum * retention * sensitivity * acquisition)
    return result


def _percentile(values, quantile):
    values = sorted(values)
    position = (len(values) - 1) * quantile
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (position - low) * (values[high] - values[low])


def evaluate(triplets: list[Triplet | dict], *, bootstrap_samples: int = 0, seed: int = 0) -> dict:
    if bootstrap_samples < 0:
        raise ValueError('bootstrap_samples must be nonnegative')
    rows = [score_triplet(triplet) for triplet in triplets]
    if len({r['triplet_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate triplet IDs would duplicate the evaluation denominator')
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['group_id']].append(row)
    per_group, family_groups = {}, defaultdict(list)
    for group, members in grouped.items():
        families = {r['family_id'] for r in members}
        if len(families) != 1:
            raise ValueError('A base group cannot belong to several evaluation families')
        family = next(iter(families))
        eligible = [r for r in members if r['eligible']]
        mean = fmean(r['GLRS'] for r in eligible) if eligible else None
        per_group[group] = {'family_id': family, 'GLRS': mean,
                            'total_triplets': len(members), 'eligible_triplets': len(eligible)}
        if mean is not None:
            family_groups[family].append(mean)
    per_family = {family: {'GLRS': fmean(scores), 'eligible_groups': len(scores)}
                  for family, scores in sorted(family_groups.items())}
    family_scores = [r['GLRS'] for r in per_family.values()]
    eligible = [r for r in rows if r['eligible']]
    ci = None
    ci_reason = 'fewer_than_two_eligible_families' if len(family_scores) < 2 else 'disabled'
    if len(family_scores) >= 2 and bootstrap_samples:
        rng = random.Random(seed)
        draws = [fmean(rng.choices(family_scores, k=len(family_scores))) for _ in range(bootstrap_samples)]
        ci = [_percentile(draws, .025), _percentile(draws, .975)]
        ci_reason = None
    return {'metric': 'GLRS-v0.1-research-candidate',
            'triplet_macro_GLRS': fmean(r['GLRS'] for r in eligible) if eligible else None,
            'group_macro_GLRS': fmean(r['GLRS'] for r in per_group.values() if r['GLRS'] is not None) if eligible else None,
            'family_macro_GLRS': fmean(family_scores) if family_scores else None,
            'family_bootstrap_95': ci, 'family_bootstrap_unavailable_reason': ci_reason,
            'bootstrap_samples': bootstrap_samples, 'bootstrap_seed': seed,
            'coverage': {'total_triplets': len(rows), 'eligible_triplets': len(eligible),
                         'eligible_fraction': len(eligible) / len(rows) if rows else None,
                         'total_groups': len(grouped), 'eligible_groups': sum(r['GLRS'] is not None for r in per_group.values()),
                         'total_families': len({r['family_id'] for r in rows}), 'eligible_families': len(per_family),
                         'failed_agent_episodes': sum(r['failed_agent_episodes'] for r in rows),
                         'missing_agent_episodes': sum(r['missing_agent_episodes'] for r in rows),
                         'eligible_triplets_with_agent_failure': sum(r['failed_agent_episodes'] > 0 for r in eligible),
                         'eligible_triplets_with_missing_prediction': sum(r['missing_agent_episodes'] > 0 for r in eligible),
                         'exclusion_reasons': dict(Counter(reason for r in rows for reason in r['exclusion_reasons']))},
            'per_group': per_group, 'per_family': per_family, 'triplets': rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline GLRS candidate scorer; gold stays evaluator-only')
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--bootstrap-samples', type=int, default=0)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding='utf-8'))
        if not isinstance(payload, list):
            raise ValueError('Input must be a JSON list of matched triplets')
        result = evaluate(payload, bootstrap_samples=args.bootstrap_samples, seed=args.seed)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
