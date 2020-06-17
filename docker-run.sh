#!/bin/bash
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

THIS_DIR=$( (cd "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) )

set -e

error() {
    echo >&2 "* Error: $*"
}

fatal() {
    error "$@"
    exit 1
}

message() {
    echo "* $*"
}

# shellcheck source=docker-config.sh
source "$THIS_DIR/docker-config.sh" || \
    fatal "Could not load configuration from $THIS_DIR/docker-config.sh"

APP=mnist-flask-app
NO_PORT=false
ENTRYPOINT=
DOCKER_OPTIONS=()
TF_SERVING_URI=

usage() {
    echo "Run $APP application"
    echo
    echo "$0 [options]"
    echo "options:"
    echo "      --no-port              Do not map ports"
    echo "                             (default: ${NO_PORT})"
    echo "      --entrypoint           Set docker entrypoint"
    echo "      --network              Set docker network"
    echo "      --tf-serving-uri       Use TF serving URI instead of local model"
    echo "      --help                 Display this help and exit"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-port)
            NO_PORT=true
            shift
            ;;
        --entrypoint)
            ENTRYPOINT=$2
            shift 2
            ;;
        --entrypoint=*)
            ENTRYPOINT=${1#*=}
            shift
            ;;
        --network)
            DOCKER_OPTIONS+=("--network=$2")
            shift 2
            ;;
        --network=*)
            DOCKER_OPTIONS+=("--network=${1#*=}")
            shift
            ;;
        --tf-serving-uri=*)
            TF_SERVING_URI=${1#*=}
            shift
            ;;
        --tf-serving-uri)
            TF_SERVING_URI=$2
            shift 2
            ;;
        --help)
            usage
            exit
            ;;
        --)
            shift
            break
            ;;
        -*)
            fatal "Unknown option $1"
            ;;
        *)
            break
            ;;
    esac
done

if [[ "$NO_PORT" != "true" ]]; then
    DOCKER_OPTIONS+=(-p 5000:5000)
fi
if [[ -n "$ENTRYPOINT" ]]; then
    DOCKER_OPTIONS+=("--entrypoint=${ENTRYPOINT}")
fi
if [[ -n "$TF_SERVING_URI" ]]; then
    DOCKER_OPTIONS+=("--env=TF_SERVING_URI=${TF_SERVING_URI}")
fi

set -xe
cd "${THIS_DIR}"
docker run --rm -ti "${DOCKER_OPTIONS[@]}" "${IMAGE_NAME}" "$@"
