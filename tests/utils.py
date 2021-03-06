from collections import defaultdict
import os
import subprocess

from conda_build.conda_interface import Resolve
from conda_build.metadata import MetaData
import networkx as nx
import pytest

test_data_dir = os.path.join(os.path.dirname(__file__), 'data')

default_meta = {'build': 0,
                'build_dependencies': {},
                'run_test_dependencies': {},
                'version': '1.0',
                }

build_dict = {'build': True, 'test': False, 'install': False, 'meta': default_meta}


@pytest.fixture(scope='function')
def testing_workdir(tmpdir, request):
    """ Create a workdir in a safe temporary folder; cd into dir above before test, cd out after

    :param tmpdir: py.test fixture, will be injected
    :param request: py.test fixture-related, will be injected (see pytest docs)
    """

    saved_path = os.getcwd()

    tmpdir.chdir()
    # temporary folder for profiling output, if any
    tmpdir.mkdir('prof')

    def return_to_saved_path():
        if os.path.isdir(os.path.join(saved_path, 'prof')):
            profdir = tmpdir.join('prof')
            files = profdir.listdir('*.prof') if profdir.isdir() else []

            for f in files:
                f.rename(os.path.join(saved_path, 'prof', f.basename))
        os.chdir(saved_path)

    request.addfinalizer(return_to_saved_path)

    return str(tmpdir)


def make_recipe(name, dependencies=()):
    os.makedirs(name)
    with open(os.path.join(name, 'meta.yaml'), 'w') as f:
        # not valid meta.yaml.  Doesn't matter for test.
        f.write('package:\n')
        f.write('   name: {0}\n'.format(name))
        f.write('   version: 1.0\n')
        if dependencies:
            f.write('requirements:\n')
            f.write('    build:\n')
            for dep in dependencies:
                f.write('        - {0}\n'.format(dep))


@pytest.fixture(scope='function')
def testing_git_repo(testing_workdir, request):
    subprocess.check_call(['git', 'init'])
    with open('sample_file', 'w') as f:
        f.write('weee')
    subprocess.check_call(['git', 'add', 'sample_file'])
    subprocess.check_call(['git', 'commit', '-m', 'commit 1'])
    os.makedirs('not_a_recipe')
    with open(os.path.join('not_a_recipe', 'testfile'), 'w') as f:
        f.write('weee')
    make_recipe('test_dir_1')
    subprocess.check_call(['git', 'add', 'test_dir_1'])
    subprocess.check_call(['git', 'commit', '-m', 'commit 2'])
    make_recipe('test_dir_2', ['test_dir_1'])
    subprocess.check_call(['git', 'add', 'test_dir_2'])
    subprocess.check_call(['git', 'commit', '-m', 'commit 3'])
    make_recipe('test_dir_3', ['test_dir_2'])
    subprocess.check_call(['git', 'add', 'test_dir_3'])
    subprocess.check_call(['git', 'commit', '-m', 'commit 4'])
    return testing_workdir


@pytest.fixture(scope='function')
def testing_graph(request):
    g = nx.DiGraph()
    for x in ['a', 'b', 'c', 'd', 'e']:
        g.add_node(x, build=False, test=False, install=False, meta=default_meta)
    # d depends on c depends on b depends on a
    g.add_edge('b', 'a')
    g.add_edge('c', 'b')
    g.add_edge('d', 'c')
    g.add_edge('e', 'd')
    g.node['b']['build'] = True
    return g


@pytest.fixture(scope='function')
def testing_conda_resolve(request):
    index = {
        "a": {
            "build": "0",
            "build_number": 0,
            "date": "2015-10-28",
            "depends": [],
            "license": "LGPL",
            "md5": "7268f7dcc075e615af758d1243ed4f1d",
            "name": "a",
            "requires": [],
            "size": 303694,
            "version": "920"
        },
        "b": {
            "build": "0",
            "build_number": 0,
            "date": "2015-10-28",
            "depends": [],
            "license": "LGPL",
            "md5": "7268f7dcc075e615af758d1243ed4f1d",
            "name": "b",
            "requires": [],
            "size": 303694,
            "version": "920"
        },
        "c": {
            "build": "0",
            "build_number": 0,
            "date": "2015-10-28",
            "depends": [],
            "license": "LGPL",
            "md5": "7268f7dcc075e615af758d1243ed4f1d",
            "name": "c",
            "requires": [],
            "size": 303694,
            "version": "920"
        },
        "d": {
            "build": "0",
            "build_number": 0,
            "date": "2015-10-28",
            "depends": [],
            "license": "LGPL",
            "md5": "7268f7dcc075e615af758d1243ed4f1d",
            "name": "d",
            "requires": [],
            "size": 303694,
            "version": "920"
        }
    }
    return Resolve(index)


@pytest.fixture(scope='function')
def testing_metadata(request):
    d = defaultdict(dict)
    d['package']['name'] = request.function.__name__
    d['package']['version'] = '1.0'
    d['build']['number'] = '1'
    d['build']['entry_points'] = []
    # MetaData does the auto stuff if the build string is None
    d['build']['string'] = None
    d['requirements']['build'] = ['build_requirement']
    d['requirements']['run'] = ['run_requirement  1.0']
    d['test']['requires'] = ['test_requirement']
    d['test']['commands'] = ['echo "A-OK"', 'exit 0']
    d['about']['home'] = "sweet home"
    d['about']['license'] = "contract in blood"
    d['about']['summary'] = "a test package"

    return MetaData.fromdict(d)
