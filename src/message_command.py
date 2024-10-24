def check_message(message: str):
    if len(message) < 1:
        return None

    if message[0] != '!':
        return None

    msg = message[1:]

    if msg == '미코피' or msg == '35P' or msg == '35p' or msg == '쥬예' or msg == '제이' or msg == '윤제이'\
            or msg == '이토빙' or msg == '슈담뒤' or msg == '원더맛':
        mkp_text = '■■■■   ■■■■   ■   ■■■■   ■■■　   ■　　■   ■■■■   ■　　■\n'
        mkp_text += '■　　　   ■　　　   ■   ■　　■   ■　　■   ■　　■   ■　　　   ■　■\n'
        mkp_text += '■■■■   ■■■■   ■   ■■■■   ■　　■   ■　　■   ■　　　   ■■\n'
        mkp_text += '　　　■   　　　■   ■   ■　　　   ■　　■   ■　　■   ■　　　   ■　■\n'
        mkp_text += '■■■■   ■■■■   ■   ■　　　   ■■■　   ■■■■   ■■■■   ■　　■'
        return mkp_text

    return None
