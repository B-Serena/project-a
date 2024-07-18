
## Conda 가상 환경 QUANDL 환경변수 설정

# 1. 가상환경 활성화
conda activate "가상환경_이름"

# 2. 환경변수 설정 (세션에만 유효)
export QUANDL_API_KEY="여기에_당신의_API_키를_넣으세요"

# 3. 환경변수 영구 설정 (가상환경에만 적용)
conda env config vars set QUANDL_API_KEY="여기에_당신의_API_키를_넣으세요"
conda env config vars set PINECONE_API_KEY="여기에_당신의_API_키를_넣으세요"
conda env config vars set PINECONE_ENVIRONMENT="여기에_당신의_ENV_를_넣으세요"

# 4. 변경사항 적용을 위해 가상환경 재활성화
conda activate "가상환경_이름"

# 5. 환경변수 확인
echo $QUANDL_API_KEY

# 6. Python에서 환경변수 확인
python -c "import os; print(os.getenv('QUANDL_API_KEY'))"