from lxml import etree

xml_bytes = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<registrationModel>\n    <peer>\n        <peer_id>test</peer_id>\n    </peer>\n    <register>true</register>\n</registrationModel>\n"""


def get_available_peers_as_xml_str(available_peers):
    root = etree.Element('registered_peers')
    # another child with text
    for peer_dict in available_peers:
        peer = etree.Element('peer')
        peer_id = etree.Element('peer_id')
        peer_id.text = peer_dict['peer_id']
        peer.append(peer_id)
        root.append(peer)

    # pretty string
    res = etree.tostring(root, pretty_print=True)
    print(res)
    return res


def parse_registration_message_from_xml(xml_obj):
    peer_id = None
    register = None
    for element in xml_obj.iter("*"):
        if element.tag == 'peer_id':
            peer_id = element.text
        elif element.tag == 'register':
            register = element.text
            if register == 'true':
                register = True
            elif register == 'false':
                register = False
            else:
                ValueError(f'unexpected value for registration parameter: {register}')
    return register, peer_id


def parse_xml(xml_as_bytes):
    return etree.fromstring(xml_as_bytes)


if __name__ == '__main__':
    root = parse_xml(xml_bytes)
    print(parse_registration_message_from_xml(root))
