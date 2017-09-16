if [ "$#" != "1" ]
then
  echo Usage: $0 \<github file name\>
  exit
fi

curl -i -X POST \
     -H "Content-Type: application/json" \
     http://localhost:7474/testing/files/$1 \
     -d @- << EOF
{
 "environment": "test"
}
EOF

