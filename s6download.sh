if [ -z ${TARGETPLATFORM} ]
then
    arch=$(uname -m)
    echo "Arch: "${arch}
    if [ "${arch}" == 'x86_64' ];
    then
    echo "X64 Architecture"
    curl -o /tmp/s6overlay.tar.gz -L https://github.com/just-containers/s6-overlay/releases/download/v2.2.0.3/s6-overlay-amd64.tar.gz
    fi
    if [ "${arch}" == 'armv7l' ];
    then
    echo "Arm architecture"
    curl -o /tmp/s6overlay.tar.gz -L https://github.com/just-containers/s6-overlay/releases/download/v2.2.0.3/s6-overlay-armhf.tar.gz
    fi
    if [ "${arch}" == 'aarch64' ];
    then
    echo "Arm64 architecture"
    curl -o /tmp/s6overlay.tar.gz -L https://github.com/just-containers/s6-overlay/releases/download/v2.2.0.3/s6-overlay-aarch64.tar.gz
    fi
else
    echo "Platform: "${TARGETPLATFORM}
    if [ "${TARGETPLATFORM}" == 'linux/amd64' ];
    then
    echo "X64 Architecture"
    curl -o /tmp/s6overlay.tar.gz -L https://github.com/just-containers/s6-overlay/releases/download/v2.2.0.3/s6-overlay-amd64.tar.gz
    fi
    if [ "${TARGETPLATFORM}" == 'linux/arm/v7' ];
    then
    echo "Arm architecture"
    curl -o /tmp/s6overlay.tar.gz -L https://github.com/just-containers/s6-overlay/releases/download/v2.2.0.3/s6-overlay-armhf.tar.gz
    fi
    if [ "${TARGETPLATFORM}" == 'linux/arm64' ];
    then
    echo "Arm64 architecture"
    curl -o /tmp/s6overlay.tar.gz -L https://github.com/just-containers/s6-overlay/releases/download/v2.2.0.3/s6-overlay-aarch64.tar.gz
    fi
fi