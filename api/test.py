"""
Vercel Test Function - 가장 기본적인 구조
"""

def handler(event, context=None):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': '{"message": "Test OK", "status": "success"}'
    }

# Vercel 호환성을 위한 추가 export
app = handler
main = handler
