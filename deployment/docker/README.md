# PacioFSLocal Docker Container

## Build
```
docker build \
  -t paciofspython \
  .;
```

## Run
```
docker run \
  --rm \
  -p=3489:3489 \
  -p=3490:3490 \
  paciofspython;
```

## Or, run and enter shell
Privileged mode (at your own risk) is needed to enable use of FUSE in the docker container. This allows the container to have root capabilities on the host machine.
```
docker run \
  -it \
  --rm \
  --privileged \
  paciofspython \
  /bin/ash;
```

## Or, run from docker hub image
```
docker run \
  --rm \
  --privileged \
  -p=3489:3489 \
  -p=3490:3490 \
  jonasspenger/paciofspython;
```
