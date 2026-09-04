"""Profile real Flask requests in an isolated temporary working directory.

Run from the project root: python tests/benchmark_requests.py.
The bundled running example is repeated to provide a reproducible workload.
"""
import cProfile
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import pstats
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import pm4py
from webapp import create_app, pages
from src import orchestrator
from src.analysis import attribute_extractor
from src.analysis.privacy import max_zoom


def run():
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        for module in (pages, orchestrator, attribute_extractor, max_zoom):
            module.FILEPATH = directory
        example = pm4py.read_xes(str(ROOT / 'data/evaluation_data/runningexample.xes'))
        copies = []
        for i in range(int(os.getenv('BENCH_COPIES', '200'))):
            frame = example.copy()
            frame['case:concept:name'] = str(i) + ':' + frame['case:concept:name'].astype(str)
            copies.append(frame)
        frame = pd.concat(copies, ignore_index=True)
        source = directory / 'input.xes'
        pm4py.write_xes(frame, str(source))
        source_bytes = source.read_bytes()
        config = {'K_EVENT': 1, 'K_EDGE': 1, 'K_TRACE': 1, 'L_DIV': 1,
                  'ENFORCE_PRIVACY': True, 'DELETE_TRACES': False,
                  'SINGLE_EVENT_L_DIV': False, 'FOlLOW_EVENT_L_DIV': False,
                  'DECOUPLE_TRACES': False, 'EXPORT_ABSTRACTED_LOG': False}
        results = {'events': len(frame)}
        app = create_app()
        app.testing = True
        client = app.test_client()
        logging.disable(logging.CRITICAL)

        def measure(name, request):
            profile = cProfile.Profile()
            start = time.perf_counter()
            response = profile.runcall(request)
            elapsed = time.perf_counter() - start
            assert response.status_code == 200, response.get_data(as_text=True)
            payload = json.dumps(response.get_json(), sort_keys=True).encode()
            if os.getenv('BENCH_OUTPUT'):
                output = Path(os.environ['BENCH_OUTPUT'])
                output.mkdir(parents=True, exist_ok=True)
                (output / f'{name}.json').write_bytes(payload)
            results[name] = {'seconds': round(elapsed, 3),
                             'sha256': hashlib.sha256(payload).hexdigest()}
            print('\nPROFILE:', name)
            pstats.Stats(profile).strip_dirs().sort_stats('cumulative').print_stats(25)

        with patch.object(pages, 'load_config', lambda: pages.config.update(config)):
            measure('upload', lambda: client.post('/api/upload_data', data={
                'file': (io.BytesIO(source_bytes), 'example.xes')}))
            abstractions = client.get('/api/available_abstractions').get_json()
            selections = [values[0] for values in abstractions.values()]
            payload = {'abstractions': selections, 'specific_zooms': []}
            measure('base', lambda: client.post('/api/abstracted_data', json=payload))
            measure('repeat', lambda: client.post('/api/abstracted_data', json=payload))
            target = 'org:resource' if 'org:resource' in abstractions else 'Resource'
            payload['specific_zooms'] = [{
                'target_column': target, 'filter_column': 'concept:name',
                'filter_attribute': '*', 'abstraction_function': abstractions[target][-1]}]
            measure('specific', lambda: client.post('/api/abstracted_data', json=payload))
        print('RESULTS', json.dumps(results, sort_keys=True))


if __name__ == '__main__':
    run()
