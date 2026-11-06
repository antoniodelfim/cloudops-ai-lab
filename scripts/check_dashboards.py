"""Valida provisionamento Grafana e sintaxe das consultas nos backends locais."""
import json
import urllib.parse
from dashboards import dashboards
from smoke import eventually, request


def main():
    for dashboard in dashboards():
        uid = dashboard['uid']
        eventually(lambda: request('http://127.0.0.1:3000/api/dashboards/uid/' + uid).get('dashboard', {}).get('uid') == uid)
        for panel in dashboard['panels']:
            if 'targets' not in panel:
                continue
            target = panel['targets'][0]
            query = urllib.parse.quote(target['query'])
            source = panel['datasource']['uid']
            if source == 'prometheus':
                result = request('http://127.0.0.1:9090/api/v1/query?query=' + query)
                assert result['status'] == 'success', json.dumps(result)
            elif source == 'loki':
                result = request('http://127.0.0.1:3100/loki/api/v1/query_range?query=' + query)
                assert result['status'] == 'success', json.dumps(result)
            else:
                request('http://127.0.0.1:3200/api/search?q=' + query)
        print('PASS estrutura e sintaxe: ' + uid + ' (não valida instrumentação da aplicação)')


if __name__ == '__main__':
    main()
