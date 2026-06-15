import os
import json

PATH = os.path.join('saves', 'scores.json')


def load_best():
    try:
        with open(PATH, encoding='utf-8') as f:
            data = json.load(f)
        return {'wave': int(data.get('wave', 0)), 'score': int(data.get('score', 0))}
    except Exception:
        return {'wave': 0, 'score': 0}


def save_best(wave, score):
    best = load_best()
    if wave > best['wave'] or (wave == best['wave'] and score > best['score']):
        try:
            os.makedirs('saves', exist_ok=True)
            with open(PATH, 'w', encoding='utf-8') as f:
                json.dump({'wave': wave, 'score': score}, f)
        except Exception:
            pass
        return True
    return False
