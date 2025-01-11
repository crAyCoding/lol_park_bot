# 몇 가지 필요한 Constant
line_names = ['탑', '정글', '미드', '원딜', '서폿']

# 현재 내전이 진행 중인지 확인
is_normal_game = False

# 일반 내전 / 피어리스 내전 / 긴급 내전 / 티어 제한 내전 / 칼바람 내전 참가자들을 담은 Log
normal_game_log = None
fearless_game_log = None
emergency_game_log = None
tier_limited_game_log = None
aram_game_log = None

# 일반 내전이 진행 중인 채널
normal_game_channel = None

# 일반 내전 / 피어리스 내전 모집 호스트
normal_game_creator = None
fearless_game_creator = None
emergency_game_creator = None
tier_limited_game_creator = None
aram_game_creator = None

# 확정된 내전 팀 리스트
finalized_normal_game_team_list = None

# 티어 제한 내전 전용
tier_limit_standard_score = None
up_and_down = None

# 칼바람 내전 전용
aram_available_champions_list = None
aram_view_message_id = None

# 20인 내전 리스트
twenty_summoner_list = None

# 20인 내전 뷰
twenty_view = None

# 20인 내전 뷰를 담은 메세지
twenty_view_message = None

# 20인 내전 호스트
twenty_host = None

# 20인 경매 dictionary
auction_dict = None

# 20인 경매 summoner만 담은 dictionary
auction_summoners_dict = None

# 20인 내전 결승 진출 팀 목록
twenty_final_teams = None

# 20인 내전 진행 여부
is_twenty_game = False

# 데이터베이스 파일 저장소
summoners_db = '/database/summoners.db'

# 롤 챔피언 이름 목록
lol_champions = [
    "aatrox", "ahri", "akali", "akshan", "alistar", "ambessa", "amumu", "anivia", "annie", "aphelios", "ashe",
    "aurelionsol", "aurora", "azir", "bard", "belveth", "blitzcrank", "brand", "braum", "briar", "caitlyn", "camille",
    "cassiopeia", "chogath", "corki", "darius", "diana", "drmundo", "draven", "ekko", "elise", 
    "evelynn", "ezreal", "fiddlesticks", "fiora", "fizz", "galio", "gankplank", "garen", "gnar", 
    "gragas", "graves", "gwen", "hecarim", "heimerdinger", "hwei", "illaoi", "irellia", "ivern", "janna", 
    "jarvaniv", "jax", "jayce", "jhin", "jinx", "ksante", "kaisa", "kalista", "karma", "karthus", 
    "kassadin", "katarina", "kayle", "kayn", "kennen", "khazix", "kindred", "kled", "kogmaw", "ksante",
    "leblanc", "leesin", "leona", "lillia", "lissandra", "lucian", "lulu", "lux", "malphite", 
    "malzahar", "maokai", "masteryi", "milio", "missfortune", "mordekaiser", "morgana", "naafiri",
    "nami", "nasus", "nautilus", "neeko", "nidalee", "nilah", "nocturne", "nunu", "olaf", 
    "orianna", "ornn", "pantheon", "poppy", "pyke", "qiyana", "quinn", "rakan", "rammus", "reksai", 
    "rell", "renataglasc", "renekton", "rengar", "riven", "rumble", "ryze", "samira", "sejuani", 
    "senna", "seraphine", "sett", "shaco", "shen", "shyvana", "singed", "sion", "sivir", "skarner", "smolder",
    "sona", "soraka", "swain", "sylas", "syndra", "tahmkench", "taliyah", "talon", "taric", 
    "teemo", "thresh", "tristana", "trundle", "tryndamere", "twistedfate", "twitch", "udyr", 
    "urgot", "varus", "vayne", "veigar", "velkoz", "vex", "vi", "viego", "viktor", "vladimir", 
    "volibear", "warwick", "wukong", "xayah", "xerath", "xinzhao", "yasuo", "yone", "yorick", 
    "yuumi", "zac", "zed", "zeri", "ziggs", "zilean", "zoe", "zyra"
]
