#!/bin/bash
set -e

# Change working directory
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/certs"
cd "$__dir"

echo "This will generate the keys based on the README instructions."
echo "And it will take into account the default structure and configuration of the docker-compose.yml file."

read -r -p "Enter the KME number (index (from 1)) for which to generate certificates: " kme_num

ca_cert=$(grep "CA_FILE=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n 1p)

# Get KME 1
kme_cert=$(grep "KME_CERT=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n "$kme_num"p)
kme_key=$(grep "KME_KEY=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n "$kme_num"p)
kme_id=$(grep "\- KME_ID=" ../docker-compose.yml | sed 's/^.*=//' | sed -n "$kme_num"p)

# Get SAE 1
sae_cert=$(grep "SAE_CERT=" ../docker-compose.yml | sed 's/^.*=//' | sed -e "s/^\/certs\///" | sed -n "$kme_num"p)
sae_id=$(grep "ATTACHED_SAE_ID=" ../docker-compose.yml | sed 's/^.*=//' | sed -n "$kme_num"p)

# List info
echo "CA: $ca_cert"

echo "KME: cert $kme_cert, key $kme_key, id $kme_id"
echo "SAE: cert $sae_cert, id $sae_id"

echo ""

read -r -p "Do you want to continue? <Y/n> " prompt

if [[ $prompt == "n" || $prompt == "N" || $prompt == "no" || $prompt == "No" ]]
then
  exit 0
fi

# Generate CA
if ! [ -e "$ca_cert" ]
then
    echo "Generating CA..."
    openssl genrsa -out ca.key 4096
    openssl req -x509 -new -nodes -key ca.key -sha256 -days 730 -out "$ca_cert" -subj '/CN=CA/O=CA/C=LV'
fi

# Generate KME
echo "Generating KME..."
openssl req -new -nodes -out kme-1.csr -newkey rsa:4096 -keyout "$kme_key" -subj "/CN=$kme_id/O=KME $kme_num/C=LV"
openssl x509 -req -in kme-1.csr -CA "$ca_cert" -CAkey ca.key -CAcreateserial -out "$kme_cert" -days 365 -sha256

# Generate SAE
echo "Generating SAE..."
openssl req -new -nodes -out sae-1.csr -newkey rsa:4096 -keyout sae-1.key -subj "/CN=$sae_id/O=SAE $kme_num/C=LV"
openssl x509 -req -in sae-1.csr -CA "$ca_cert" -CAkey ca.key -CAcreateserial -out "$sae_cert" -days 365 -sha256