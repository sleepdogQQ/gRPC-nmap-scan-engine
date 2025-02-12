openssl genrsa -out server.key 2048
openssl req -new -x509 -sha256 -key server.key \
              -out server.crt -days 3650
openssl req -new -sha256 -key server.key -out server.csr
openssl x509 -req -sha256 -in server.csr -signkey server.key \
               -out server.crt -days 3650
