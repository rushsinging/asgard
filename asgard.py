# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

from sh import helm
from os import path, environ

import profig

import click

CONFIG_FILE = path.join(environ.get('HOME'), '.asgard/config')


@click.group()
@click.pass_context
def asgard(ctx):
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
    cfg = profig.Config(CONFIG_FILE)
    cfg.sync()

    click.echo(click.style('Init Helm ...', fg='yellow'))
    helm.init('-c')
    click.echo(click.style('Init Helm [OK]', fg='green'))

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
    ))


@asgard.command()
@click.pass_context
def fetch(ctx):
    pass


@asgard.command()
@click.pass_context
def package(ctx):
    # curl -F "chart=@mychart-0.1.0.tgz" http://localhost:8080/api/charts
    pass


@asgard.command()
@click.option('--release', '-r', default='')
@click.argument('chart')
@click.pass_context
def install(ctx, release,chart):
    click.echo(click.style('Updating Helm ...', fg='yellow'))
    helm.repo.update()
    click.echo(click.style('Updating Helm [OK]', fg='green'))

    click.echo(helm.install(
        '--host', ctx.obj.get('tiller_host'),
        '--name', release or chart,
        '%s/%s' % (ctx.obj.get('helm_repo'), chart),
    ))


@asgard.command()
@click.argument('release')
@click.pass_context
def delete(ctx, release):
    click.echo(helm.delete(
        '--host', ctx.obj.get('tiller_host'), release, '--purge'
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
        release or chart, '%s/%s' % (ctx.obj.get('helm_repo'), chart),
    ))


if __name__ == '__main__':
    asgard(obj={})
