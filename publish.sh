#!/bin/bash

devpi use http://pypi.iguokr.com/guokr/dev/+simple
devpi login guokr --password guokr
devpi upload
devpi upload --formats bdist_wheel
