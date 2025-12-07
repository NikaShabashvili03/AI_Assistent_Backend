import re
IPv4_REGEX = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
IPv6_REGEX = re.compile(r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$')

def is_connected(me, other):
    from accounts.models import Connection
    u1, u2 = sorted([me, other], key=lambda x: x.id)
    return Connection.objects.filter(user1=u1, user2=u2).exists()

def is_valid_ip(ip):
    if IPv4_REGEX.match(ip):
        # Further check each octet is 0-255
        parts = ip.split('.')
        for part in parts:
            if not 0 <= int(part) <= 255:
                return False
        return True
    elif IPv6_REGEX.match(ip):
        return True
    return False

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    if ip and is_valid_ip(ip):
        return ip
    
    return None

def get_lang_from_path(request):
    match = re.match(r'^/([a-z]{2})/', request.path)
    return match.group(1) if match else 'en'
