# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

import json
from functools import partial
from os import path, environ
from sh import helm, curl, rm

import profig

import click

CONFIG_FILE = path.join(environ.get('HOME'), '.asgard/config')


@click.group()
@click.pass_context
def asgard(ctx):
    '''
    Asgard -- Deploy tool on k8s ,helm and chartmuseum.
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
    Init and set asgard's config.
    '''
    cfg = profig.Config(CONFIG_FILE)
    cfg.sync()

    click.echo(click.style('Init Helm ...', fg='yellow'))
    helm.init('-c')
    click.echo(click.style('Init Helm [OK]', fg='green'))

    setting_key = 'helm.kube_context'
    kube_context = click.prompt(
        'Please the name of your k8s context',
        default=cfg.get(setting_key))
    cfg[setting_key] = kube_context

    setting_key = 'helm.chart_repo'
    chart_repo = click.prompt(
        'Please enter uri for chart repo',
        default=cfg.get(setting_key))
    cfg[setting_key] = chart_repo

    setting_key = 'helm.tiller_host'
    tiller_host = click.prompt(
        'Please enter uri for tiller',
        default=cfg.get(setting_key))
    cfg[setting_key] = tiller_host

    setting_key = 'helm.tiller_namespace'
    tiller_namespace = click.prompt(
        'Please enter namespace for tiller',
        default=cfg.get(setting_key))
    cfg[setting_key] = tiller_namespace

    setting_key = 'helm.helm_repo'
    helm_repo = click.prompt(
        'Please enter the default helm repo',
        default=cfg.get(setting_key))
    cfg[setting_key] = helm_repo

    cfg.sync()


@asgard.command()
@click.pass_context
def list(ctx):
    click.echo(helm.list(
        '--host', ctx.obj.get('tiller_host'),
        '--tiller-namespace', ctx.obj.get('tiller_namespace'),
        '--kube-context', ctx.obj.get('kube_context'),
    ))


@asgard.command()
@click.argument('chart')
@click.pass_context
def fetch(ctx, chart):
    helm.fetch('--untar', '%s/%s' % (ctx.obj.get('helm_repo'), chart))


@asgard.command()
@click.argument('path')
@click.argument('version')
@click.pass_context
def package(ctx, path, version):
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
