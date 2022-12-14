from typing import Mapping, Tuple, Union, IO
import magic
from lxml import etree
from traceback import print_exc
import re , json

from ehforwarderbot import MsgType, Chat
from ehforwarderbot.chat import ChatMember
from ehforwarderbot.message import Substitutions, Message, LinkAttribute, LocationAttribute

def efb_text_simple_wrapper(text: str, ats: Union[Mapping[Tuple[int, int], Union[Chat, ChatMember]], None] = None) -> Message:
    """
    A simple EFB message wrapper for plain text. Emojis are presented as is (plain text).
    :param text: The content of the message
    :param ats: The substitutions of at messages, must follow the Substitution format when not None
                [[begin_index, end_index], {Chat or ChatMember}]
    :return: EFB Message
    """
    efb_msg = Message(
        type=MsgType.Text,
        text=text
    )
    if ats:
        efb_msg.substitutions = Substitutions(ats)
    return efb_msg

def efb_image_wrapper(file: IO, filename: str = None, text: str = None) -> Message:
    """
    A EFB message wrapper for images.
    :param file: The file handle
    :param filename: The actual filename
    :param text: The attached text
    :return: EFB Message
    """
    efb_msg = Message()
    efb_msg.file = file
    mime = magic.from_file(file.name, mime=True)
    if isinstance(mime, bytes):
        mime = mime.decode()

    if "gif" in mime:
        efb_msg.type = MsgType.Animation
    else:
        efb_msg.type = MsgType.Image

    if filename:
        efb_msg.filename = filename
    else:
        efb_msg.filename = file.name
        efb_msg.filename += '.' + str(mime).split('/')[1]

    if text:
        efb_msg.text = text

    efb_msg.path = efb_msg.file.name
    efb_msg.mime = mime
    return efb_msg

def efb_video_wrapper(file: IO, filename: str = None, text: str = None) -> Message:
    """
    A EFB message wrapper for voices.
    :param file: The file handle
    :param filename: The actual filename
    :param text: The attached text
    :return: EFB Message
    """
    efb_msg = Message()
    efb_msg.type = MsgType.Video
    efb_msg.file = file
    mime = magic.from_file(file.name, mime=True)
    if isinstance(mime, bytes):
        mime = mime.decode()
    if filename:
        efb_msg.filename = filename
    else:
        efb_msg.filename = file.name
        efb_msg.filename += '.' + str(mime).split('/')[1]  # Add extension suffix
    efb_msg.path = efb_msg.file.name
    efb_msg.mime = mime
    if text:
        efb_msg.text = text
    return efb_msg

def efb_file_wrapper(file: IO, filename: str = None, text: str = None) -> Message:
    """
    A EFB message wrapper for voices.
    :param file: The file handle
    :param filename: The actual filename
    :param text: The attached text
    :return: EFB Message
    """
    efb_msg = Message()
    efb_msg.type = MsgType.File
    efb_msg.file = file
    mime = magic.from_file(file.name, mime=True)
    if isinstance(mime, bytes):
        mime = mime.decode()
    if filename:
        efb_msg.filename = filename
    else:
        efb_msg.filename = file.name
        efb_msg.filename += '.' + str(mime).split('/')[1]  # Add extension suffix
    efb_msg.path = efb_msg.file.name
    efb_msg.mime = mime
    if text:
        efb_msg.text = text
    return efb_msg


def efb_share_link_wrapper(text: str) -> Message:
    """
    ??????msgType49?????? - ??????xml, xml ??? //appmsg/type ????????????????????????.
    /msg/appmsg/type
    ?????????
    //appmsg/type = 1 : ??????????????????
    //appmsg/type = 2 : ????????????
    //appmsg/type = 3 : ????????????
    //appmsg/type = 4 : ???????????????
    //appmsg/type = 5 : ???????????????????????????
    //appmsg/type = 6 : ?????? ?????????????????????????????????????????????????????????)??????????????? msgType = 10000 ????????????????????????????????????????????????????????????????????????????????????????????????????????????
    //appmsg/type = 8 : ?????????????????????
    //appmsg/type = 17 : ??????????????????
    //appmsg/type = 19 : ???????????????????????????
    //appmsg/type = 21 : ????????????
    //appmsg/type = 24 : ???????????????????????????
    //appmsg/type = 33 : ????????????
    //appmsg/type = 35 : ????????????
    //appmsg/type = 36 : ???????????????????????????
    //appmsg/type = 51 : ?????????????????????????????????
    //appmsg/type = 53 : ????????????????????????
    //appmsg/type = 57 : ??????(??????)????????????????????????????????????????????????????????? id 
    //appmsg/type = 63 : ?????????????????????????????????
    //appmsg/type = 74 : ?????? (??????????????????????????????)
    //appmsg/type = 87 : ?????????
    //appmsg/type = 2000 : ??????
    :param text: The content of the message
    :return: EFB Message
    """

    xml = etree.fromstring(text)
    result_text = ""
    try: 
        type = int(xml.xpath('/msg/appmsg/type/text()')[0])
        if type in [ 1 , 2 ]:
            title = xml.xpath('/msg/appmsg/title/text()')[0]
            des = xml.xpath('/msg/appmsg/des/text()')[0]
            efb_msg = Message(
                type = MsgType.Text,
                text = title if title==des else title+" :\n"+des,
            )
        elif type == 3: #????????????
            try:
                music_name = xml.xpath('/msg/appmsg/title/text()')[0]
                music_singer = xml.xpath('/msg/appmsg/des/text()')[0]
            except:
                efb_msg = Message(
                    type = MsgType.Text,
                    text = "- - - - - - - - - - - - - - - \n?????????????????????",
                )
            try:
                thumb_url = xml.xpath('/msg/appmsg/url/text()')[0]
                attribute = LinkAttribute(
                    title = music_name + ' / ' + music_singer,
                    description = None,
                    url = thumb_url ,
                    image = None
                )
                efb_msg = Message(
                    attributes=attribute,
                    type=MsgType.Link,
                    text= None,
                    vendor_specific={ "is_mp": False }
                )
            except:
                pass
        elif type in [ 4 , 36 ]: # ??????????????????????????? , ???????????? , ????????????
            title = xml.xpath('/msg/appmsg/title/text()')[0]
            try:
                des = xml.xpath('/msg/appmsg/des/text()')[0]
            except:
                des = ""
            url = xml.xpath('/msg/appmsg/url/text()')[0]
            app = xml.xpath('/msg/appinfo/appname/text()')[0]
            description = f"{des}\n---- from {app}"
            attribute = LinkAttribute(
                title = title,
                description = description,
                url = url ,
                image = None
            )
            efb_msg = Message(
                attributes=attribute,
                type=MsgType.Link,
                text= None,
                vendor_specific={ "is_mp": False }
            )
        elif type == 5: # xml??????
            if len(xml.xpath('/msg/appmsg/showtype/text()'))!=0:
                showtype = int(xml.xpath('/msg/appmsg/showtype/text()')[0])
            else:
                showtype = 0
            if showtype == 0: # ??????????????????(???????????????????????????????????????, ?????????????????????)
                title = url = des = thumburl = None # ?????????
                try:
                    try:
                        title = xml.xpath('/msg/appmsg/title/text()')[0]
                    except:
                        title = "[xml ?????????????????????????????????]"
                    if '<' in title and '>' in title:
                        subs = re.findall('<[\s\S]+?>', title)
                        for sub in subs:
                            title = title.replace(sub, '')
                    url = xml.xpath('/msg/appmsg/url/text()')[0]
                    if len(xml.xpath('/msg/appmsg/des/text()'))!=0:
                        des = xml.xpath('/msg/appmsg/des/text()')[0]
                    if len(xml.xpath('/msg/appmsg/thumburl/text()'))!=0:
                        thumburl = xml.xpath('/msg/appmsg/thumburl/text()')[0]
                    if len(xml.xpath('/msg/appinfo/appname/text()'))!=0:
                        app = xml.xpath('/msg/appinfo/appname/text()')[0]
                        des = f"{des}\n---- from {app}"

                    if len(xml.xpath('/msg/appmsg/sourceusername/text()'))!=0:
                        sourceusername = xml.xpath('/msg/appmsg/sourceusername/text()')[0]
                        try:
                            sourcedisplayname = xml.xpath('/msg/appmsg/sourcedisplayname/text()')[0]
                            result_text += f"\n??????????????????[{sourcedisplayname}(id: {sourceusername})]\n\n"
                        except:
                            result_text += f"\n??????????????????[{sourcedisplayname}]\n\n"
                except Exception as e:
                    print_exc()
                if title is not None and url is not None:
                    attribute = LinkAttribute(
                        title=title,
                        description=des,
                        url=url,
                        image=thumburl
                    )
                    efb_msg = Message(
                        attributes=attribute,
                        type=MsgType.Link,
                        text=result_text,
                        vendor_specific={ "is_mp": True }
                    )
            elif showtype == 1: # ?????????????????????
                items = xml.xpath('//item')
                for item in items:
                    title = url = digest = cover = None # ?????????
                    try:
                        title = item.find("title").text
                        url = item.find("url").text
                        digest = item.find("digest").text
                        cover = item.find("cover").text
                    except Exception as e:
                        print_exc()
                    
                    if '@app' in text:
                        name = xml.xpath('//publisher/nickname/text()')[0]
                        digest += f"\n- - - - from {name}"
                    if title and url:
                        attribute = LinkAttribute(
                            title=title,
                            description=digest,
                            url=url,
                            image= cover,
                        )
                        efb_msg = Message(
                            attributes=attribute,
                            type=MsgType.Link,
                            text=result_text,
                            vendor_specific={ "is_mp": True }
                        )
                    else: # ???????????????????????????url??????
                        result_text += f"{title}\n  - - - - - - - - - - - - - - - \n{digest}"
                        efb_msg = Message(
                            type=MsgType.Text,
                            text=result_text
                        )
        elif type == 8:
            efb_msg = Message(
                type=MsgType.Unsupported,
                text='????????????????????? ????????????????????????',
            )
        elif type == 19: # ???????????????????????????
            try:
                msg_title = xml.xpath('/msg/appmsg/title/text()')[0]
            except:
                msg_title = ""
            forward_content = xml.xpath('/msg/appmsg/des/text()')[0]
            result_text += f"{msg_title}\n\n{forward_content}"
            efb_msg = Message(
                type=MsgType.Text,
                text= result_text,
                vendor_specific={ "is_forwarded": True }
            )
        elif type == 21: # ????????????
            msg_title = xml.xpath('/msg/appmsg/title/text()')[0].strip("<![CDATA[??????").strip("??????]]>")
            if '??????' not in msg_title:
                msg_title = msg_title.strip()
                efb_msg = Message(
                    type=MsgType.Text,
                    text= msg_title ,
                )
            else:
                rank = xml.xpath('/msg/appmsg/hardwareinfo/messagenodeinfo/rankinfo/rank/rankdisplay/text()')[0].strip("<![CDATA[").strip("]]>")
                steps = xml.xpath('/msg/appmsg/hardwareinfo/messagenodeinfo/rankinfo/score/scoredisplay/text()')[0].strip("<![CDATA[").strip("]]>")
                result_text += f"{msg_title}\n\n??????: {rank}\n??????: {steps}"
                efb_msg = Message(
                    type=MsgType.Text,
                    text=result_text,
                    vendor_specific={ "is_wechatsport": True }
                )
        elif type == 24:
            desc = xml.xpath('/msg/appmsg/des/text()')[0]
            recorditem = xml.xpath('/msg/appmsg/recorditem/text()')[0]
            xml = etree.fromstring(recorditem)
            datadesc = xml.xpath('/recordinfo/datalist/dataitem/datadesc/text()')[0]
            efb_msg = Message(
                type=MsgType.Text,
                text= '???????????? :\n  - - - - - - - - - - - - - - - \n' +desc + '\n' + datadesc,
                vendor_specific={ "is_mp": True }
            )
        elif type == 33:
            sourcedisplayname = xml.xpath('/msg/appmsg/sourcedisplayname/text()')[0]
            weappiconurl = xml.xpath('/msg/appmsg/weappinfo/weappiconurl/text()')[0]
            url = xml.xpath('/msg/appmsg/url/text()')[0]
            attribute = LinkAttribute(
                title=sourcedisplayname,
                description=None,
                url=url,
                image=weappiconurl
            )
            efb_msg = Message(
                attributes=attribute,
                type=MsgType.Link,
                text=None,
                vendor_specific={ "is_mp": True }
            )
        elif type == 35:
            efb_msg = Message(
                type=MsgType.Text,
                text= '???????????? : ????????????',
                vendor_specific={ "is_mp": False }
            )  
        elif type == 40: # ?????????????????????
            title = xml.xpath('/msg/appmsg/title/text()')[0]
            desc = xml.xpath('/msg/appmsg/des/text()')[0]
            efb_msg = Message(
                type=MsgType.Text,
                text= f"{title}\n\n{desc}" ,
                vendor_specific={ "is_forwarded": True }
            )
        elif type == 51: # ?????????????????????????????????
            title = xml.xpath('/msg/appmsg/title/text()')[0]
            url = xml.xpath('/msg/appmsg/url/text()')[0]
            if len(xml.xpath('/msg/appmsg/finderFeed/avatar/text()'))!=0:
                imgurl = xml.xpath('/msg/appmsg/finderFeed/avatar/text()')[0].strip("<![CDATA[").strip("]]>")
            else:
                imgurl = None
            if len(xml.xpath('/msg/appmsg/finderFeed/desc/text()'))!=0:
                desc = xml.xpath('/msg/appmsg/finderFeed/desc/text()')[0]
            else:
                desc = None
            result_text += f"?????????????????????\n - - - - - - - - - - - - - - - \n"
            attribute = LinkAttribute(
                title=title,
                description=  '\n' + desc,
                url= url,
                image= imgurl
            )
            efb_msg = Message(
                attributes=attribute,
                type=MsgType.Link,
                text=result_text,
                vendor_specific={ "is_mp": True }
            )
        elif type == 57: # ????????????????????????
            msg = xml.xpath('/msg/appmsg/title/text()')[0]
            refer_msgType = int(xml.xpath('/msg/appmsg/refermsg/type/text()')[0]) # ?????????????????????
            # refer_fromusr = xml.xpath('/msg/appmsg/refermsg/fromusr/text()')[0] # ???????????????????????????
            # refer_fromusr = xml.xpath('/msg/appmsg/refermsg/chatusr/text()')[0] # ?????????????????????????????????
            refer_displayname = xml.xpath('/msg/appmsg/refermsg/displayname/text()')[0] # ????????????????????????????????????
            if refer_msgType == 1: # ???????????????????????????
                refer_content = xml.xpath('/msg/appmsg/refermsg/content/text()')[0] # ?????????????????????
                result_text += f"???{refer_displayname}: {refer_content}???\n  - - - - - - - - - - - - - - - \n{msg}"
            else: # ?????????????????????????????????????????????
                result_text += f"???{refer_displayname}: ????????????: ??????????????????????????????,?????????????????????\n  - - - - - - - - - - - - - - - \n{msg}"
            efb_msg = Message(
                type=MsgType.Text,
                text=result_text,
                vendor_specific={ "is_refer": True }
            )
        elif type == 63: # ?????????????????????????????????
            title = xml.xpath('/msg/appmsg/title/text()')[0]
            url = xml.xpath('/msg/appmsg/url/text()')[0]
            imgurl = xml.xpath('/msg/appmsg/finderLive/headUrl/text()')[0].strip("<![CDATA[").strip("]]>")
            desc = xml.xpath('/msg/appmsg/finderLive/desc/text()')[0].strip("<![CDATA[").strip("]]>")
            result_text += f"?????????????????????\n  - - - - - - - - - - - - - - - \n"
            attribute = LinkAttribute(
                title=title,
                description= '\n' + desc ,
                url= url,
                image= imgurl
            )
            efb_msg = Message(
                attributes=attribute,
                type=MsgType.Link,
                text=result_text,
                vendor_specific={ "is_mp": True }
            )
        elif type == 87: # ?????????
            title = xml.xpath('/msg/appmsg/textannouncement/text()')[0]
            efb_msg = Message(
                type=MsgType.Text,
                text= f"[?????????]:\n{title}" ,
                vendor_specific={ "is_mp": False }
            )
        elif type == 2000:
            subtype = xml.xpath("/msg/appmsg/wcpayinfo/paysubtype/text()")[0]
            money =  xml.xpath("/msg/appmsg/wcpayinfo/feedesc/text()")[0].strip("<![CDATA[").strip("]]>")
            if subtype == "1":
                efb_msg = Message(
                    type=MsgType.Text,
                    text= f"?????????????????? {money} ???",
                    vendor_specific={ "is_mp": False }
                )
            elif subtype == "3":
                efb_msg = Message(
                    type=MsgType.Text,
                    text= f"?????????????????? {money} ???",
                    vendor_specific={ "is_mp": False }
                )
            elif subtype == "4":
                efb_msg = Message(
                    type=MsgType.Text,
                    text= f"?????????????????? {money} ???",
                    vendor_specific={ "is_mp": False }
                )
    except Exception as e:
        print_exc()

    try:
        return efb_msg
    except:
        efb_msg = Message(
            type=MsgType.Text,
            text=text
        )
        return efb_msg

def efb_location_wrapper(msg: str) -> Message:
    efb_msg = Message()
    label = re.search('''label="(.*?)"''', msg).group(1)
    x = re.search('''x="(.*?)"''', msg).group(1)
    y = re.search('''y="(.*?)"''', msg).group(1)
    efb_msg.text = label
    efb_msg.attributes = LocationAttribute(latitude=float(x),
                                           longitude=float(y))
    efb_msg.type = MsgType.Location
    return efb_msg

def efb_qqmail_wrapper(text: str) -> Message:
    xml = etree.fromstring(text)
    result_text = ""
    sender = xml.xpath('/msg/pushmail/content/sender/text()')[0].strip("<![CDATA[").strip("]]>")
    subjectwithCDATA = xml.xpath('/msg/pushmail/content/subject/text()')
    if len(subjectwithCDATA) != 0:
        subject = subjectwithCDATA[0].strip("<![CDATA[").strip("]]>")
    digest = xml.xpath('/msg/pushmail/content/digest/text()')[0].strip("<![CDATA[").strip("]]>")
    addr = xml.xpath('/msg/pushmail/content/fromlist/item/addr/text()')[0]
    datereceive = xml.xpath('/msg/pushmail/content/date/text()')[0].strip("<![CDATA[").strip("]]>")
    result_text = f"?????????{subject}\nfrom: {sender}\n????????????: {datereceive}\n??????: {digest}"
    attribute = LinkAttribute(
        title= f'??????: {addr}',
        description= result_text,
        url= f"mailto:{addr}",
        image= None
    )
    efb_msg = Message(
        attributes=attribute,
        type=MsgType.Link,
        text=None,
        vendor_specific={ "is_mp": False }
    )
    return efb_msg

def efb_miniprogram_wrapper(text: str) -> Message:
    xml = etree.fromstring(text)
    result_text = ""
    title = xml.xpath('/msg/appmsg/title/text()')[0]
    programname = xml.xpath('/msg/appmsg/sourcedisplayname/text()')[0]
    imgurl = xml.xpath('/msg/appmsg/weappinfo/weappiconurl/text()')[0].strip("<![CDATA[").strip("]]>")
    url = xml.xpath('/msg/appmsg/url/text()')[0]
    result_text = f"from: {programname}\n  - - - - - - - - - - - - - - - \n?????????????????????"
    attribute = LinkAttribute(
        title= f'{title}',
        description= result_text,
        url= url,
        image= imgurl
    )
    efb_msg = Message(
        attributes=attribute,
        type=MsgType.Link,
        text=None,
        vendor_specific={ "is_mp": False }
    )
    return efb_msg

def efb_unsupported_wrapper( text : str) -> Message:
    """
    A simple EFB message wrapper for unsupported message
    :param text: The content of the message
    :return: EFB Message
    """
    efb_msg = Message(
        type=MsgType.Unsupported,
        text=text
    )
    return efb_msg

def efb_voice_wrapper(file: IO, filename: str = None, text: str = None) -> Message:
    """
    A EFB message wrapper for voices.
    :param file: The file handle
    :param filename: The actual filename
    :param text: The attached text
    :return: EFB Message
    """
    efb_msg = Message()
    efb_msg.type = MsgType.Audio
    efb_msg.file = file
    mime = magic.from_file(efb_msg.file.name, mime=True)
    if isinstance(mime, bytes):
        mime = mime.decode()
    if filename:
        efb_msg.filename = filename
    else:
        efb_msg.filename = file.name
        efb_msg.filename += '.' + str(mime).split('/')[1]  # Add extension suffix
    efb_msg.path = efb_msg.file.name
    efb_msg.mime = mime
    if text:
        efb_msg.text = text
    return efb_msg

def efb_other_wrapper(text: str) -> Union[Message, None]:
    """
    A simple EFB message wrapper for other message
    :param text: The content of the message
    :return: EFB Message or None
    """

    xml = etree.fromstring(text)
    efb_msg = None
    try:
        msg_type = xml.xpath('/sysmsg/@type')[0]
    except:
        return None

    if msg_type == "NewXmlAddForcePush":
        userIcon = xml.xpath('/sysmsg/userIcon/text()')[0]
        desc = xml.xpath('/sysmsg/description/text()')[0]

        extinfo = json.loads(xml.xpath('/sysmsg/extInfo/text()')[0])
        auth_icon_url = extinfo["auth_icon_url"]
        nickname = extinfo["nickname"]

        attribute = LinkAttribute(
            title = nickname,
            description = desc,
            url = auth_icon_url ,
            image = userIcon
        )
        efb_msg = Message(
            attributes=attribute,
            type=MsgType.Link,
            text= None,
            vendor_specific={ "is_mp": False }
        )
    elif msg_type == "voipmt" or msg_type == "multivoip":
        if "banner" in text:
            return None
        efb_msg = efb_text_simple_wrapper("[??????/?????? ????????????]")
    elif msg_type == "delchatroommember":
        content = xml.xpath('//plain/text()')[0]
        efb_msg = efb_text_simple_wrapper(content)
    elif msg_type == "roomtoolstips":
        if str(xml.xpath('/sysmsg/todo/op/text()')[0]) == "0":
            efb_msg = efb_text_simple_wrapper("[??????????????????]")
        elif str(xml.xpath('/sysmsg/todo/op/text()')[0]) == "1":
            efb_msg = efb_text_simple_wrapper("[??????????????????]")
    elif msg_type == "paymsg":
        try:
            paymsg_type = str(xml.xpath('/sysmsg/paymsg/PayMsgType/text()')[0])
        except:
            paymsg_type = ""
        if paymsg_type == "9":
            status = xml.xpath('/sysmsg/paymsg/status/text()')[0]
            displayname = xml.xpath('/sysmsg/paymsg/displayname/text()')[0]
            if str(status) == "0":
                efb_msg = efb_text_simple_wrapper(f"[{displayname} ??????????????????]")
            if str(status) == "1":
                efb_msg = efb_text_simple_wrapper(f"[{displayname} ?????????????????????]")
            elif str(status) == "2":
                efb_msg = efb_text_simple_wrapper(f"[{displayname} ?????????????????????]")
        if "?????????" in text and "??????" in text:
            efb_msg = efb_text_simple_wrapper("[??????????????????????????????]")
        
    elif msg_type == "carditemmsg":
        msg_type = xml.xpath('/sysmsg/carditemmsg/msg_type/text()')[0]
        if str(msg_type) == "15":
            title = xml.xpath('/sysmsg/carditemmsg/title/text()')[0]
            desc = xml.xpath('/sysmsg/carditemmsg/description/text()')[0]
            url = xml.xpath('/sysmsg/carditemmsg/logo_url/text()')[0]
            attribute = LinkAttribute(
            title = title,
            description = desc,
            url = url,
            image = None
            )
            efb_msg = Message(
            attributes=attribute,
            type=MsgType.Link,
            text= None,
            vendor_specific={ "is_mp": False }
            )

    if efb_msg:
        return efb_msg
    else:
        return None