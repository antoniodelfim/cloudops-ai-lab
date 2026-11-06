"""Invariantes de isolamento e contratos dos manifestos gerados."""
import importlib.util
from pathlib import Path
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

spec = importlib.util.spec_from_file_location('infra', Path(__file__).resolve().parents[1] / 'scripts/infra.py')
infra = importlib.util.module_from_spec(spec)
spec.loader.exec_module(infra)


class Infrastructure(unittest.TestCase):
    def setUp(self):
        self.items = infra.manifests()['items']

    def test_no_secret_value_in_manifests(self):
        self.assertFalse(any(x['kind'] == 'Secret' for x in self.items))

    def test_persistent_components_have_claims_and_limits(self):
        claims = {(x['metadata']['namespace'], x['metadata']['name']) for x in self.items if x['kind'] == 'PersistentVolumeClaim'}
        for item in self.items:
            if item['kind'] != 'Deployment':
                continue
            pod = item['spec']['template']['spec']
            for volume in pod['volumes']:
                if 'persistentVolumeClaim' in volume:
                    self.assertIn((item['metadata']['namespace'], volume['persistentVolumeClaim']['claimName']), claims)
            for container in pod['containers']:
                self.assertIn('limits', container['resources'])
                self.assertNotIn(':latest', container['image'])

    def test_investigator_cannot_read_secrets_or_mutate(self):
        role = next(x for x in self.items if x['kind'] == 'Role' and x['metadata']['name'] == 'incident-investigator')
        self.assertEqual(role['metadata']['namespace'], 'apps')
        for rule in role['rules']:
            self.assertLessEqual(set(rule['verbs']), {'get', 'list'})
            self.assertNotIn('secrets', rule['resources'])
            self.assertNotIn('pods/exec', rule['resources'])

    def test_service_ports_match_container_ports(self):
        deployments = {x['metadata']['name']: x for x in self.items if x['kind'] == 'Deployment'}
        for item in self.items:
            if item['kind'] == 'Service':
                container = deployments[item['metadata']['name']]['spec']['template']['spec']['containers'][0]
                ports = {p['containerPort'] for p in container['ports']}
                self.assertTrue(all(p['targetPort'] in ports for p in item['spec']['ports']))


if __name__ == '__main__':
    unittest.main()
