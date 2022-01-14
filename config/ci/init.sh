#!/bin/bash

set -e

if [ -z $(which wget) ]; then
    # use curl
    GET='curl'
else
    GET='wget -O -'
fi

# Pull in the server code.
git clone --single-branch --depth 1 https://github.com/intermine/intermine.git server

export PSQL_USER=test
export PSQL_PWD=test
export KEYSTORE=${PWD}/keystore.jks

echo "#---> Running unit tests"

sudo -u postgres createuser test
sudo -u postgres psql -c "alter user test with encrypted password 'test';"

# Set up properties
PROPDIR=$HOME/.intermine
TESTMODEL_PROPS=$PROPDIR/testmodel.properties
SED_SCRIPT='s/PSQL_USER/test/'

mkdir -p $PROPDIR

echo "#--- creating $TESTMODEL_PROPS"
cp server/config/testmodel.properties $TESTMODEL_PROPS
sed -i -e $SED_SCRIPT $TESTMODEL_PROPS

# We will need a fully operational web-application
echo '#---> Building and releasing web application to test against'
(cd server/testmine && ./setup.sh)
# Travis is so slow
sleep 90 # let webapp startup

# Warm up the keyword search by requesting results, but ignoring the results
$GET "$TESTMODEL_URL/service/search" > /dev/null
# Start any list upgrades
$GET "$TESTMODEL_URL/service/lists?token=test-user-token" > /dev/null
