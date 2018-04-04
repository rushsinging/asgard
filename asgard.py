# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

import json
from functools import partial
from os import path, environ

from semantic_version import Version
import profig
import click

import sys
if sys.version > '3':
    PY3 = True
else:
    PY3 = False

try:
    from sh import curl, rm, cat
except:
    from pbs import curl, rm, cat

CONFIG_FILE = environ.get(
    'ASGARD_CONFIG', path.join(
        environ.get('VIRTUAL_ENV', environ.get('HOME', '')),
        '.asgard/config'))

def get_chart_repo(helm_repo):
    if PY3:
        repo_list = str(helm.repo.list().stdout, encoding='utf-8')
    else:
        repo_list = str(helm.repo.list().stdout)

    for l in repo_list.split('\n')[1:]:
        if not l:
            continue

        name, repo = l.split()
        if name == helm_repo:
            return repo

def get_release(release, tiller_host):
    if PY3:
        release_list = str(helm.list('--host', tiller_host).stdout, encoding='utf-8')
    else:
        release_list = str(helm.list('--host', tiller_host).stdout)

    for l in release_list.split('\n')[1:]:
        if not l:
            continue

        name, v, _ = l.split('\t', 2)
        if name.strip() == release:
            return v.strip()

def get_chart_version(helm_repo, path, version=''):
    click.echo(click.style('Updating Helm ...', fg='yellow'))
    helm.repo.update()
    click.echo(click.style('Updating Helm [OK]', fg='green'))
    if PY3:
        repo_list = str(helm.search(path).stdout, encoding='utf-8')
    else:
        repo_list = helm.search(path).stdout

    chart = '%s/%s' % (helm_repo, path)
    for l in repo_list.split('\n')[1:]:
        l = l.strip()
        if not l:
            continue

        target, version, v = l.split()[:3]
        if target == chart:
            return version
    return '0.0.0'


try:
    from sh import helm
except:
    click.echo(click.style('*** Can\'t find helm in $PATH. Please install it. ***', fg='red'))
    helm = None


@click.group()
# TODO: Add global config, e.g., 'host', 'kube-context'
@click.pass_context
def asgard(ctx):
    '''
    Asgard -- A deploy tool bases on k8s ,helm and chartmuseum.
    Run `asgard init` first if this is your first time to use.
    '''
    cmd = ctx.invoked_subcommand
    keyword = 'helm'
    if cmd == 'init':
        return

    if not path.isfile(CONFIG_FILE):
        click.echo(click.style('Run init first', fg='red'))
        return

    cfg = profig.Config(CONFIG_FILE)
    cfg.sync()
    if cfg.section(keyword).get('chart_repo'):
        click.echo(click.style('WARNING: the config `chart_repo` has been desperate!\n', fg='yellow'))

    if not environ.get('VIRTUAL_ENV'):
        click.echo(click.style('WARNING: You are using global settings!\n', fg='yellow'))

    ctx.obj.update(cfg.section(keyword))


@asgard.command()
@click.pass_context
def init(ctx):
    '''
    Init and set asgard's config. Please run and follow it.
    '''
    cfg = profig.Config(CONFIG_FILE)
    cfg.sync()

    click.echo(click.style('Init Helm ...', fg='yellow'))
    helm.init('-c')
    click.echo(click.style('Init Helm [OK]', fg='green'))

    setting_key = 'helm.kube_context'
    kube_context = click.prompt(
        'Please the name of your k8s context',
        default=cfg.get(setting_key, ''))
    cfg[setting_key] = kube_context

    setting_key = 'helm.tiller_host'
    tiller_host = click.prompt(
        'Please enter uri for tiller',
        default=cfg.get(setting_key, ''))
    cfg[setting_key] = tiller_host

    setting_key = 'helm.tiller_namespace'
    tiller_namespace = click.prompt(
        'Please enter namespace for tiller',
        default=cfg.get(setting_key, ''))
    cfg[setting_key] = tiller_namespace

    setting_key = 'helm.helm_repo'
    helm_repo = click.prompt(
        'Please enter the default helm repo',
        default=cfg.get(setting_key))
    cfg[setting_key] = helm_repo

    cfg.sync()


@asgard.command()
@click.pass_context
def info(ctx):
    '''
    Show Aagard's config.
    '''

    click.echo(click.style(CONFIG_FILE + ' :', fg='yellow'))
    click.echo()
    click.echo(cat(CONFIG_FILE))

@asgard.command()
@click.pass_context
def list(ctx):
    '''
    List releases already deployed.
    '''
    click.echo(helm.list(
        '--host', ctx.obj.get('tiller_host'),
        '--tiller-namespace', ctx.obj.get('tiller_namespace'),
        '--kube-context', ctx.obj.get('kube_context'),
    ))


@asgard.command()
@click.option('--version', '-v', default='')
@click.argument('chart')
@click.pass_context
def fetch(ctx, version, chart):
    '''
    Fetch a chart and untar to current directory.
    '''
    click.echo(click.style('Updating Helm ...', fg='yellow'))
    helm.repo.update()
    click.echo(click.style('Updating Helm [OK]', fg='green'))

    fetch_version = version or get_chart_version(ctx.obj.get('helm_repo'), chart)
    click.echo(click.style('Fetching %s@%s' % (chart, fetch_version), fg='yellow'))
    args = ['--untar', '%s/%s' % (ctx.obj.get('helm_repo'), chart)]
    if version:
        args.append('--version')
        args.append(version)
    helm.fetch(args)
    click.echo(click.style('SUCCESS!', fg='green'))

@asgard.command()
@click.argument('path')
@click.pass_context
def lint(ctx, path):
    '''
    Check chart.
    '''
    click.echo(helm.lint(path))


@asgard.command()
@click.argument('keyword')
@click.pass_context
def search(ctx, keyword):
    '''
    Search chart.
    '''
    click.echo(helm.search(keyword))


@asgard.command()
@click.argument('path')
@click.argument('version', default='')
@click.pass_context
def package(ctx, path, version):
    '''
    Package a current path to a new version and upload to chart repo.
    '''
    # helm package --app-version 0.1.9 --version 0.1.9 fantuan-base
    # curl -F "chart=@mychart-0.1.0.tgz" http://localhost:8080/api/charts

    path = path.strip('/')

    if not version:
        click.echo(click.style('No version specified. Reading from chart_repo ...', fg='yellow'))
        version = Version(get_chart_version(ctx.obj.get('helm_repo'), path))
        version = str(version.next_patch())
        click.echo(click.style('Get new version %s' % version, fg='green'))

    click.echo(click.style('Packaging ...', fg='yellow'))
    helm.package('--app-version', version, '--version', version, path)
    tar = '%s-%s.tgz' % (path, version)

    click.echo(click.style('Uploading ...', fg='yellow'))
    cmd_result = curl('-F', 'chart=@%s' % tar, get_chart_repo(ctx.obj.get('helm_repo')) + '/api/charts')

    click.echo(click.style('Cleaning ...', fg='yellow'))
    rm(tar)

    result = json.loads(cmd_result.stdout)
    if result.get('saved'):
        click.echo(click.style('SUCCESS!', fg='green'))
    else:
        click.echo(click.style('FAILED!: %s' % result.get('error'), fg='red'))


@asgard.command()
@click.argument('release')
@click.pass_context
def delete(ctx, release):
    '''
    Delete a release.
    '''
    click.echo(helm.delete(
        '--host', ctx.obj.get('tiller_host'),
        '--tiller-namespace', ctx.obj.get('tiller_namespace'),
        '--kube-context', ctx.obj.get('kube_context'),
        release, '--purge'
    ))


@asgard.command()
@click.option('--release', '-r', default='')
@click.option('--version', '-v', default='')
@click.option('--dry_run', is_flag=True, default=False)
@click.argument('chart')
@click.pass_context
def upgrade(ctx, release, version, dry_run, chart):
    '''
    Upgrade a release.
    '''
    click.echo(click.style('Updating Helm ...', fg='yellow'))
    helm.repo.update()
    click.echo(click.style('Updating Helm [OK]', fg='green'))

    # TODO: 参数
    # TODO: 批量更新

    click.echo(click.style(
        'Release %s \'s current revision is %s' % (
            release or chart, get_release(release or chart, ctx.obj.get('tiller_host'))),
        fg='green'))
    click.echo(click.style('Updating %s to %s ...' % (
        release or chart, version or get_chart_version(ctx.obj.get('helm_repo'), release or chart)),
        fg='yellow'))
    click.echo(helm.upgrade(
        '--host', ctx.obj.get('tiller_host'),
        '--tiller-namespace', ctx.obj.get('tiller_namespace'),
        '--kube-context', ctx.obj.get('kube_context'),
        '--timeout', '10', '--force', '--recreate-pods', '--wait',
        '-i', release or chart, '%s/%s' % (ctx.obj.get('helm_repo'), chart),
    ))


if __name__ == '__main__':
    asgard(obj={})
else:
    asgard = partial(asgard, obj={})
