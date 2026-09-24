#!/usr/bin/env python3
# run_batter.py — 破甲测试执行器 v2(双靶直连provider)
# 用法: python3 run_batter.py deepseek|gpt [ammo_ids...] [--rounds N]
# 结果: results/<target>_<ts>.json + 自动评分
import json, sys, os, time, urllib.request, importlib.util

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
spec = importlib.util.spec_from_file_location('score', os.path.join(BASE, 'score.py'))
score_mod = importlib.util.module_from_spec(spec)
sys.argv = ['score.py']
spec.loader.exec_module(score_mod)

# provider配置(key从160的codex-env.sh获取后填到这里,或环境变量)
PROVIDERS = {
    'deepseek': {'base': 'https://supeai.top/v1', 'model': 'deepseek-v4.1-flash', 'key_env': 'SUPEAI_TOP_KEY'},
    'gpt':      {'base': 'https://supeai.cc/v1',  'model': 'gpt-5.2-codex',       'key_env': 'SUPEAI_CC_KEY'},
}

def call(base, key, model, user, system, timeout=180):
    body = {'model': model, 'messages': []}
    if system:
        body['messages'].append({'role': 'system', 'content': system})
    body['messages'].append({'role': 'user', 'content': user})
    req = urllib.request.Request(
        f'{base}/chat/completions',
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'},
        method='POST')
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read())['choices'][0]['message']['content']

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'deepseek'
    cfg = PROVIDERS[target]
    key = os.environ.get(cfg['key_env'], '')
    if not key:
        print(f'缺少 {cfg["key_env"]} 环境变量'); sys.exit(1)
    ammo = json.load(open(os.path.join(BASE, 'ammo_matrix.json'), encoding='utf-8'))
    ids = [a for a in sys.argv[2:] if not a.startswith('--')] or list(ammo.keys())
    rounds = 3 if '--rounds' not in sys.argv else int(sys.argv[sys.argv.index('--rounds')+1])
    os.makedirs(os.path.join(BASE, 'results'), exist_ok=True)
    out = {}
    for aid in ids:
        a = ammo.get(aid)
        if not a: continue
        scores, responses = [], []
        for rd in range(rounds):
            try:
                resp = call(cfg['base'], key, cfg['model'], a['user'], a.get('system'))
                s = score_mod.score(resp)
                scores.append(s); responses.append(resp)
                print(f'  [{aid}] r{rd+1}: {s["level"]} ASR={s["ASR"]}')
                time.sleep(2)
            except Exception as e:
                print(f'  [{aid}] r{rd+1}: ERR {str(e)[:100]}')
                time.sleep(5)
        if scores:
            avg_asr = sum(s['ASR'] for s in scores) / len(scores)
            out[aid] = {'desc': a['desc'], 'avg_ASR': round(avg_asr, 2),
                        'levels': [s['level'] for s in scores],
                        'responses': responses}
            print(f'[{aid}] 最终ASR={avg_asr:.2f}')
    ts = int(time.time())
    fp = os.path.join(BASE, 'results', f'{target}_{ts}.json')
    json.dump(out, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('结果:', fp)
    # 汇总
    print(f'\n===== {target} 汇总 =====')
    for aid, r in sorted(out.items(), key=lambda x: -x[1]['avg_ASR']):
        print(f'  {r["avg_ASR"]:.2f}  {aid} ({r["desc"]})')

if __name__ == '__main__':
    main()
