# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

import json
from functools import partial
from os import path, environ
from sh import curl, rm, cat, bash

import profig

import click

CONFIG_FILE = environ.get('ASGARD_CONFIG', path.join(environ.get('HOME'), '.asgard/config'))

def get_chart_repo(helm_repo):
    repo_list = helm.repo.list().stdout

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
@click.argument('chart')
@click.pass_context
def fetch(ctx, chart):
    '''
    Fetch a chart and untar to current directory.
    '''
    helm.fetch('--untar', '%s/%s' % (ctx.obj.get('helm_repo'), chart))


@asgard.command()
@click.argument('path')
@click.argument('version')
@click.pass_context
def package(ctx, path, version):
    '''
    Package a current path to a new version and upload to chart repo.
    '''
    # helm package --app-version 0.1.9 --version 0.1.9 fantuan-base
    # curl -F "chart=@mychart-0.1.0.tgz" http://localhost:8080/api/charts

    click.echo(click.style('Packaging ...', fg='yellow'))
    helm.package('--app-version', version, '--version', version, path)
    tar = '%s-%s.tgz' % (path, version)

    click.echo(click.style('Uploading ...', fg='yellow'))
    cmd_result = curl('-F', 'chart=@%s' % tar, ctx.obj.get('chart_repo') + '/api/charts')

    click.echo(click.style('Cleaning ...', fg='yellow'))
    rm(tar)

    result = json.loads(cmd_result.stdout)
    if result.get('saved'):
        click.echo(click.style('SUCCESS!', fg='green'))
    else:
        click.echo(click.style('FAILED!: %s' % result.get('error'), fg='red'))


@asgard.command()
@click.option('--release', '-r', default='', help='the name of the release to add')
@click.argument('chart')
@click.pass_context
def install(ctx, release,chart):
    '''
    Deploy a release from a chart.
    '''
    click.echo(click.style('Updating Helm ...', fg='yellow'))
    helm.repo.update()
    click.echo(click.style('Updating Helm [OK]', fg='green'))

    click.echo(helm.install(
        '--host', ctx.obj.get('tiller_host'),
        '--tiller-namespace', ctx.obj.get('tiller_namespace'),
        '--kube-context', ctx.obj.get('kube_context'),
        '--name', release or chart,
        '%s/%s' % (ctx.obj.get('helm_repo'), chart),
    ))


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
@click.argument('chart')
@click.pass_context
def upgrade(ctx, release, chart):
    '''
    Upgrade a release.
    '''
    click.echo(click.style('Updating Helm ...', fg='yellow'))
    helm.repo.update()
    click.echo(click.style('Updating Helm [OK]', fg='green'))

    click.echo(helm.upgrade(
        '--host', ctx.obj.get('tiller_host'),
        '--tiller-namespace', ctx.obj.get('tiller_namespace'),
        '--kube-context', ctx.obj.get('kube_context'),
        release or chart, '%s/%s' % (ctx.obj.get('helm_repo'), chart),
    ))


if __name__ == '__main__':
    asgard(obj={})
else:
    asgard = partial(asgard, obj={})
