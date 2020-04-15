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
