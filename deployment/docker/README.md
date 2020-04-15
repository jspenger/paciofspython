# PacioFSLocal Docker Container

## Build
```
docker build \
  -t paciofs \
  .;
```

## Run
```
docker run \
  --rm \
  -p=3489:3489 \
  -p=3490:3490 \
  paciofs;
```

## Or, run and enter shell
```
docker run \
  -it \
  --rm \
  --privileged \
  paciofs \
  /bin/ash;
```

## Or, run from docker hub image
```
docker run \
  --rm \
  -p=3489:3489 \
  -p=3490:3490 \
  jonasspenger/paciofs;
```
