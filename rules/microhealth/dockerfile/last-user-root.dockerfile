FROM alpine:3.20 AS build
# ok: dockerfile.last-user-root
USER root
RUN apk add --no-cache build-base
FROM alpine:3.20
# ok: dockerfile.last-user-root
USER root
RUN apk add --no-cache ca-certificates
# ok: dockerfile.last-user-root
USER 10001:10001
RUN id
# ruleid: dockerfile.last-user-root
USER root
RUN chown -R 10001 /app
# ruleid: dockerfile.last-user-root
USER root
CMD ["/app/run"]
RUN echo done
# ruleid: dockerfile.last-user-root
USER 0
