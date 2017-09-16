URL=http://localhost:7474/testing/files/$(basename $(mktemp))
echo $URL


curl -i -X POST \
     -H "Content-Type: application/json" ${URL} \
     -d @- << EOF
{
 "environment": "test"
}
EOF


curl -i -X DELETE ${URL}
