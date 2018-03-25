# -*- coding: utf-8 -*-
# from __future__ import unicode_literals

from sh import helm

import click


@click.group()
@click.pass_context
def helm(ctx):
    pass


@helm.command()
@click.pass_context
def init(ctx):
    pass


@helm.command()
@click.pass_context
def fetch(ctx):
    pass


@helm.command()
@click.pass_context
def upload(ctx):
    pass


@helm.command()
@click.pass_context
def install(ctx):
    pass


if __name__ == '__main__':
    helm()
