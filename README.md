# sophys-auth

External authorization service for bluesky http-server built on top of FastAPI and SQLModel.

## TODO

- [ ] Decide on how to populate the database
- [ ] Query tsau for role updates
- [ ] Background task update db from tsau
- [ ] Setup some <sql> database
- [ ] Tepuiless deployment
- [ ] Dockerfile

## DONE

- [x] Setup FastAPI and SQLModel
- [x] Setup base table models
- [x] Use sqlite for development
- [x] Setup basic CRUD operations
- [x] Build authorization dict from db entries
- [x] `/instrument/{beamline}/qserver/access` bluesky endpoint
