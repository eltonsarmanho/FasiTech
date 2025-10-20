import json
import base64

# Seu JSON original
def convertJsonToBase64(json_data):
    # Converter o dicionário JSON em uma string JSON
    #json_string = json.dumps(json_data)

    # Codificar a string JSON em Base64
    base64_encoded = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

    return base64_encoded

def convertBase64ToJson(base64_string):
    # Decodificar a string Base64 de volta para JSON
    json_string = base64.b64decode(base64_string).decode('utf-8')
    json_data = json.loads(json_string)

    return json_data
