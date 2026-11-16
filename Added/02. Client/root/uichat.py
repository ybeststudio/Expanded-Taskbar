if __USE_DYNAMIC_MODULE__:
	import pyapi

app = __import__(pyapi.GetModuleName("app"))
chr = __import__(pyapi.GetModuleName("chr"))
net = __import__(pyapi.GetModuleName("net"))

import ui
import grp
import chat
import wndMgr
import ime
import localeInfo
import colorInfo
import constInfo
import systemSetting

if app.ENABLE_EMOTICONS_SYSTEM:
	import uiEmoticons

ENABLE_CHAT_COMMAND = TRUE
ENABLE_LAST_SENTENCE_STACK = TRUE
ENABLE_INSULT_CHECK = TRUE

chatInputSetList = []
def InsertChatInputSetWindow(wnd):
	global chatInputSetList
	chatInputSetList.append(wnd)

def RefreshChatMode():
	global chatInputSetList
	map(lambda wnd:wnd.OnRefreshChatMode(), chatInputSetList)

def DestroyChatInputSetWindow():
	global chatInputSetList
	chatInputSetList = []

## ChatModeButton
class ChatModeButton(ui.Window):

	OUTLINE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)
	OVER_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 0.3)
	BUTTON_STATE_UP = 0
	BUTTON_STATE_OVER = 1
	BUTTON_STATE_DOWN = 2

	def __init__(self):
		ui.Window.__init__(self)
		self.state = None
		self.buttonText = None
		self.event = None
		self.SetWindowName("ChatModeButton")

		if not app.ENABLE_MULTILANGUAGE_CHATTING:
			net.EnableChatInsultFilter(ENABLE_INSULT_CHECK)

	def __del__(self):
		ui.Window.__del__(self)

	def SAFE_SetEvent(self, event):
		self.event=ui.__mem_func__(event)

	def SetText(self, text):
		if None == self.buttonText:
			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetWindowHorizontalAlignCenter()
			textLine.SetWindowVerticalAlignCenter()
			textLine.SetVerticalAlignCenter()
			textLine.SetHorizontalAlignCenter()
			textLine.SetPackedFontColor(self.OUTLINE_COLOR)
			textLine.Show()
			self.buttonText = textLine

		self.buttonText.SetText(text)

	def SetSize(self, width, height):
		self.width = width
		self.height = height
		ui.Window.SetSize(self, width, height)

	def OnMouseOverIn(self):
		self.state = self.BUTTON_STATE_OVER

	def OnMouseOverOut(self):
		self.state = self.BUTTON_STATE_UP

	def OnMouseLeftButtonDown(self):
		self.state = self.BUTTON_STATE_DOWN

	def OnMouseLeftButtonUp(self):
		self.state = self.BUTTON_STATE_UP
		if self.IsIn():
			self.state = self.BUTTON_STATE_OVER

		if None != self.event:
			self.event()

	def OnRender(self):

		(x, y) = self.GetGlobalPosition()

		grp.SetColor(self.OUTLINE_COLOR)
		grp.RenderRoundBox(x, y, self.width, self.height)

		if self.state >= self.BUTTON_STATE_OVER:
			grp.RenderRoundBox(x+1, y, self.width-2, self.height)
			grp.RenderRoundBox(x, y+1, self.width, self.height-2)

			if self.BUTTON_STATE_DOWN == self.state:
				grp.SetColor(self.OVER_COLOR)
				grp.RenderBar(x+1, y+1, self.width-2, self.height-2)

## ChatLine
class ChatLine(ui.EditLine):

	CHAT_MODE_NAME = {	chat.CHAT_TYPE_TALKING : localeInfo.CHAT_NORMAL,
						chat.CHAT_TYPE_PARTY : localeInfo.CHAT_PARTY,
						chat.CHAT_TYPE_GUILD : localeInfo.CHAT_GUILD,
						chat.CHAT_TYPE_SHOUT : localeInfo.CHAT_SHOUT, }

	def __init__(self):
		self.interface = None
		ui.EditLine.__init__(self)
		self.SetWindowName("Chat Line")

		if app.ENABLE_EMOTICONS_SYSTEM:
			self.SetFontName("Tahoma:12")
			# self.SetVerticalAlignCenter()

		self.lastShoutTime = 0
		self.eventEscape = lambda *arg: None
		self.eventReturn = lambda *arg: None
		self.eventTab = None
		self.chatMode = chat.CHAT_TYPE_TALKING
		self.bCodePage = TRUE

		if app.ENABLE_EMOTICONS_SYSTEM:
			self.refreshEmoticons = None

		self.overTextLine = ui.TextLine()
		self.overTextLine.SetParent(self)
		if app.ENABLE_EMOTICONS_SYSTEM:
			self.overTextLine.SetPosition(0, 0)
		else:
			self.overTextLine.SetPosition(-1, 0)
		self.overTextLine.SetFontColor(1.0, 1.0, 0.0)
		self.overTextLine.SetOutline()
		self.overTextLine.Hide()

		self.lastSentenceStack = []
		self.lastSentencePos = 0

	if app.ENABLE_EMOTICONS_SYSTEM:
		def SetEmoticonsListBoard(self, emoticons):
			self.refreshEmoticons = emoticons

		def DelEmoticonsListBoard(self):
			self.refreshEmoticons = None

	def SetChatMode(self, mode):
		self.chatMode = mode

	def GetChatMode(self):
		return self.chatMode

	def ChangeChatMode(self):
		if chat.CHAT_TYPE_TALKING == self.GetChatMode():
			self.SetChatMode(chat.CHAT_TYPE_PARTY)
			self.SetText("#")
			self.SetEndPosition()

		elif chat.CHAT_TYPE_PARTY == self.GetChatMode():
			self.SetChatMode(chat.CHAT_TYPE_GUILD)
			self.SetText("%")
			self.SetEndPosition()

		elif chat.CHAT_TYPE_GUILD == self.GetChatMode():
			self.SetChatMode(chat.CHAT_TYPE_SHOUT)
			self.SetText("!")
			self.SetEndPosition()

		elif chat.CHAT_TYPE_SHOUT == self.GetChatMode():
			self.SetChatMode(chat.CHAT_TYPE_TALKING)
			self.SetText("")

		self.__CheckChatMark()

	def GetLink(self, text):
		link = ""
		start = text.find("http://")
		if start == -1:
			start = text.find("https://")
		if start == -1:
			return ""

		return text[start:len(text)].split(" ")[0]

	def GetCurrentChatModeName(self):
		try:
			return self.CHAT_MODE_NAME[self.chatMode]
		except:
			import exception
			exception.Abort("ChatLine.GetCurrentChatModeName")

	def SAFE_SetEscapeEvent(self, event):
		self.eventEscape = ui.__mem_func__(event)

	def SAFE_SetReturnEvent(self, event):
		self.eventReturn = ui.__mem_func__(event)

	def SAFE_SetTabEvent(self, event):
		self.eventTab = ui.__mem_func__(event)

	def SetTabEvent(self, event):
		self.eventTab = event

	def OpenChat(self):
		self.SetFocus()
		self.__ResetChat()

	def __ClearChat(self):
		self.SetText("")
		self.lastSentencePos = 0

	def __ResetChat(self):
		if chat.CHAT_TYPE_PARTY == self.GetChatMode():
			self.SetText("#")
			self.SetEndPosition()
		elif chat.CHAT_TYPE_GUILD == self.GetChatMode():
			self.SetText("%")
			self.SetEndPosition()
		elif chat.CHAT_TYPE_SHOUT == self.GetChatMode():
			self.SetText("!")
			self.SetEndPosition()
		else:
			self.__ClearChat()

		self.__CheckChatMark()

	def __SendChatPacket(self, text, type, langID = 0):
		if net.IsChatInsultIn(text):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHAT_INSULT_STRING)
		else:
			link = self.GetLink(text)
			if link != "":
				if not chr.IsGameMaster():
					text = text.replace(link, "|cFF00C0FC|h|Hweb:" + link.replace("://", "XxX") + "|h" + link + "|h|r")
				else:
					text = text.replace(link, "|cFF00C0FC|h|Hsysweb:" + link.replace("://", "XxX") + "|h" + link + "|h|r")

			if app.ENABLE_MULTILANGUAGE_CHATTING:
				net.SendChatPacket(text, type, langID)
			else:
				net.SendChatPacket(text, type)

			if app.ENABLE_EMOTICONS_SYSTEM:
				chat.SaveEmojisChat(text)
				if self.refreshEmoticons:
					self.refreshEmoticons.RefreshCategory(0)

	def __SendPartyChatPacket(self, text, langID = 0):

		if 1 == len(text):
			self.RunCloseEvent()
			return

		self.__SendChatPacket(text[1:], chat.CHAT_TYPE_PARTY, langID)
		self.__ResetChat()

	def __SendGuildChatPacket(self, text, langID = 0):

		if 1 == len(text):
			self.RunCloseEvent()
			return

		self.__SendChatPacket(text[1:], chat.CHAT_TYPE_GUILD, langID)
		self.__ResetChat()

	def __SendShoutChatPacket(self, text, langID = 0):

		if 1 == len(text):
			self.RunCloseEvent()
			return

		if app.GetTime() < self.lastShoutTime + 15:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CHAT_SHOUT_LIMIT)
			self.__ResetChat()
			return

		self.__SendChatPacket(text[1:], chat.CHAT_TYPE_SHOUT, langID)
		self.__ResetChat()

		self.lastShoutTime = app.GetTime()

	def __SendTalkingChatPacket(self, text, langID = 0):
		self.__SendChatPacket(text, chat.CHAT_TYPE_TALKING, langID)
		self.__ResetChat()

	def OnIMETab(self):
		interface = self.interface
		if app.ENABLE_CHAT_TABS and interface and interface.wndChat:
			interface.wndChat.ToggleStopChat()
			return TRUE
		return FALSE

	def OnIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self)

		if app.ENABLE_EMOTICONS_SYSTEM:
			if self.GetTextSize()[0] > 430:
				ime.PasteBackspace()

		self.__CheckChatMark()

	def __CheckChatMark(self):

		self.overTextLine.Hide()

		text = self.GetText()
		if len(text) > 0:
			if '#' == text[0]:
				self.overTextLine.SetText("#")
				self.overTextLine.Show()
			elif '%' == text[0]:
				self.overTextLine.SetText("%")
				self.overTextLine.Show()
			elif '!' == text[0]:
				self.overTextLine.SetText("!")
				self.overTextLine.Show()

	def OnIMEKeyDown(self, key):
		if app.VK_UP == key:
			self.__PrevLastSentenceStack()
			return TRUE

		if app.VK_DOWN == key:
			self.__NextLastSentenceStack()
			return TRUE

		ui.EditLine.OnIMEKeyDown(self, key)

	def __PrevLastSentenceStack(self):
		if self.lastSentencePos < chat.GetChatStackSize():
			self.lastSentencePos += 1
			lastSentence = chat.GetChatStack(self.lastSentencePos)
			self.SetText(lastSentence)
			self.SetEndPosition()

	def __NextLastSentenceStack(self):
		if self.lastSentencePos > 1:
			self.lastSentencePos -= 1
			lastSentence = chat.GetChatStack(self.lastSentencePos)
			self.SetText(lastSentence)
			self.SetEndPosition()

	def __PushLastSentenceStack(self, text):
		global ENABLE_LAST_SENTENCE_STACK
		if not ENABLE_LAST_SENTENCE_STACK:
			return

		if len(text) <= 0:
			return

		LAST_SENTENCE_STACK_SIZE = 32
		if len(self.lastSentenceStack) > LAST_SENTENCE_STACK_SIZE:
			self.lastSentenceStack.pop(0)

		self.lastSentenceStack.append(text)
		chat.AppendChatStack(text)

	def OnIMEReturn(self):
		text = self.GetText()
		textLen = len(text)

		if app.ENABLE_EMOTICONS_SYSTEM:
			if self.GetTextSize()[0] > 430:
				return

		self.__PushLastSentenceStack(text)

		textSpaceCount=text.count(' ')

		if (textLen > 0) and (textLen != textSpaceCount):
			langID = 0
			if app.ENABLE_MULTILANGUAGE_CHATTING:
				langID = self.GetInputSystemLangID()

			if '#' == text[0]:
				self.__SendPartyChatPacket(text, langID)
			elif '%' == text[0]:
				self.__SendGuildChatPacket(text, langID)
			elif '!' == text[0]:
				self.__SendShoutChatPacket(text, langID)
			else:
				self.__SendTalkingChatPacket(text, langID)
		else:
			self.__ClearChat()
			self.eventReturn()

		return TRUE

	def OnPressEscapeKey(self):
		self.__ClearChat()
		self.eventEscape()
		return TRUE

	def RunCloseEvent(self):
		self.eventEscape()

	def BindInterface(self, interface):
		self.interface = interface

	def OnMouseLeftButtonDown(self):
		hyperlink = ui.GetHyperlink()
		if hyperlink:
			if app.IsPressed(app.DIK_LALT):
				link = chat.GetLinkFromHyperlink(hyperlink)
				ime.PasteString(link)
			else:
				self.interface.MakeHyperlinkTooltip(hyperlink)
		else:
			ui.EditLine.OnMouseLeftButtonDown(self)

class ChatInputSet(ui.Window):

	CHAT_OUTLINE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)

	def __init__(self):
		ui.Window.__init__(self)
		self.SetWindowName("ChatInputSet")

		InsertChatInputSetWindow(self)
		self.__Create()

	def __del__(self):
		ui.Window.__del__(self)

	def __Create(self):
		chatModeButton = ChatModeButton()
		chatModeButton.SetParent(self)
		chatModeButton.SetSize(40, 17)
		chatModeButton.SetText(localeInfo.CHAT_NORMAL)
		chatModeButton.SetPosition(7, 2)
		chatModeButton.SAFE_SetEvent(self.OnChangeChatMode)
		self.chatModeButton = chatModeButton

		chatLine = ChatLine()
		chatLine.SetParent(self)
		if app.ENABLE_EMOTICONS_SYSTEM:
			chatLine.SetMax(770)
			chatLine.SetUserMax(110)
		else:
			chatLine.SetMax(512)
			chatLine.SetUserMax(76)
		chatLine.SetText("")
		chatLine.SAFE_SetTabEvent(self.OnChangeChatMode)
		chatLine.x = 0
		chatLine.y = 0
		chatLine.width = 0
		chatLine.height = 0
		self.chatLine = chatLine

		btnSend = ui.Button()
		btnSend.SetParent(self)
		btnSend.SetUpVisual("d:/ymir work/ui/game/taskbar/Send_Chat_Button_01.sub")
		btnSend.SetOverVisual("d:/ymir work/ui/game/taskbar/Send_Chat_Button_02.sub")
		btnSend.SetDownVisual("d:/ymir work/ui/game/taskbar/Send_Chat_Button_03.sub")
		if app.ENABLE_EMOTICONS_SYSTEM:
			toolTipbtnSend = ui.Ballon()
			toolTipbtnSend.SetParent(btnSend)
			toolTipbtnSend.SetPosition(0, -38)
			toolTipbtnSend.SetWindowHorizontalAlignCenter()
			toolTipbtnSend.Hide()
			toolTipbtnSend.SetText(localeInfo.CHAT_SEND_CHAT)
			self.toolTipbtnSend = toolTipbtnSend
			btnSend.SetToolTipWindow(self.toolTipbtnSend)
		else:
			btnSend.SetToolTipText(localeInfo.CHAT_SEND_CHAT)
		btnSend.SAFE_SetEvent(self.chatLine.OnIMEReturn)
		self.btnSend = btnSend

	def Destroy(self):
		self.chatModeButton = None
		self.chatLine = None
		self.btnSend = None

	def Open(self):
		self.chatLine.Show()
		if app.ENABLE_CHAT_TABS:
			self.chatLine.SetPosition(57, 5)
		elif app.ENABLE_EMOTICONS_SYSTEM:
			self.chatLine.SetPosition(77, 5)
		else:
			self.chatLine.SetPosition(57, 5)
		self.chatLine.SetFocus()
		self.chatLine.OpenChat()

		self.chatModeButton.SetPosition(7, 2)
		self.chatModeButton.Show()

		self.btnSend.Show()
		self.Show()

		self.RefreshPosition()
		return TRUE

	def Close(self):
		self.chatLine.KillFocus()
		self.chatLine.Hide()
		self.chatModeButton.Hide()
		self.btnSend.Hide()
		self.Hide()
		return TRUE

	def SetEscapeEvent(self, event):
		self.chatLine.SetEscapeEvent(event)

	def SetReturnEvent(self, event):
		self.chatLine.SetReturnEvent(event)

	def OnChangeChatMode(self):
		RefreshChatMode()

	def OnRefreshChatMode(self):
		self.chatLine.ChangeChatMode()
		self.chatModeButton.SetText(self.chatLine.GetCurrentChatModeName())

	def SetChatFocus(self):
		self.chatLine.SetFocus()

	def KillChatFocus(self):
		self.chatLine.KillFocus()

	def SetChatMax(self, max):
		self.chatLine.SetUserMax(max)

	def RefreshPosition(self):
		if app.ENABLE_CHAT_TABS:
			self.chatLine.SetSize(self.GetWidth() - 194, 13)
			self.btnSend.SetPosition(self.GetWidth() - 125, 2)
		elif app.ENABLE_EMOTICONS_SYSTEM:
			self.chatLine.SetSize(self.GetWidth() - 113, 13)
			self.btnSend.SetPosition(self.GetWidth() - 25, 2)
		else:
			self.chatLine.SetSize(self.GetWidth() - 93, 13)
			self.btnSend.SetPosition(self.GetWidth() - 25, 2)
		(self.chatLine.x, self.chatLine.y, self.chatLine.width, self.chatLine.height) = self.chatLine.GetRect()

	def BindInterface(self, interface):
		self.chatLine.BindInterface(interface)

	def OnRender(self):
		(x, y, width, height) = self.chatLine.GetRect()
		if app.ENABLE_EMOTICONS_SYSTEM:
			ui.RenderRoundBox(x - 4, y - 3, width + 7, height + 5, self.CHAT_OUTLINE_COLOR)
		else:
			ui.RenderRoundBox(x - 4, y - 3, width + 7, height + 4, self.CHAT_OUTLINE_COLOR)

## ChatWindow
class ChatWindow(ui.Window):

	BOARD_START_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.0)
	BOARD_END_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.8)
	BOARD_MIDDLE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.5)
	CHAT_OUTLINE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)

	EDIT_LINE_HEIGHT = 25
	CHAT_WINDOW_WIDTH = 600
	if app.ENABLE_CHAT_TABS:
		CHAT_WINDOW_WIDTH = 650
		CHAT_LINE_STEP = 15

	if app.ENABLE_EMOTICONS_SYSTEM:
		LINE_HEIGHT = 0

	class ChatBackBoard(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
		def __del__(self):
			ui.Window.__del__(self)

	class ChatButton(ui.DragButton):

		def __init__(self):
			ui.DragButton.__init__(self)
			self.AddFlag("float")
			self.AddFlag("movable")
			self.AddFlag("restrict_x")
			self.topFlag = FALSE
			self.SetWindowName("ChatWindow:ChatButton")

		def __del__(self):
			ui.DragButton.__del__(self)

		def SetOwner(self, owner):
			self.owner = owner

		def OnMouseOverIn(self):
			app.SetCursor(app.VSIZE)

		def OnMouseOverOut(self):
			app.SetCursor(app.NORMAL)

		def OnTop(self):
			if TRUE == self.topFlag:
				return

			self.topFlag = TRUE
			self.owner.SetTop()
			self.topFlag = FALSE

	def __init__(self):
		self.emojiPicker = None
		self.chatTabLine = None
		self.tabToolTip = None
		self.chatTabLineRight = None
		self.chatTabLineExtra = []
		if app.ENABLE_CHAT_TABS:
			self.stopChatText = None
			self.chatTabSelected = [0]
		ui.Window.__init__(self)
		self.AddFlag("float")

		self.SetWindowName("ChatWindow")
		self.__RegisterChatColorDict()

		self.boardState = chat.BOARD_STATE_VIEW
		self.chatID = chat.CreateChatSet(chat.CHAT_SET_CHAT_WINDOW)
		chat.SetBoardState(self.chatID, chat.BOARD_STATE_VIEW)

		if app.ENABLE_EMOTICONS_SYSTEM:
			chat.SetStep(self.chatID, 20)
			chat.SetFontNameChat("Tahoma:12")
		if app.ENABLE_CHAT_TABS:
			chat.SetStep(self.chatID, self.CHAT_LINE_STEP)

		self.xBar = 0
		self.yBar = 0
		self.widthBar = 0
		self.heightBar = 0
		self.curHeightBar = 0
		self.visibleLineCount = 0
		self.scrollBarPos = 1.0
		self.scrollLock = FALSE

		if app.ENABLE_EMOTICONS_SYSTEM:
			emoticonsBoard = uiEmoticons.EmoticonsBoard()
			emoticonsBoard.SetParent(self)
			self.emoticonsBoard = emoticonsBoard

		chatInputSet = ChatInputSet()
		chatInputSet.SetParent(self)
		chatInputSet.SetEscapeEvent(ui.__mem_func__(self.CloseChat))
		chatInputSet.SetReturnEvent(ui.__mem_func__(self.CloseChat))
		if app.ENABLE_CHAT_TABS:
			chatInputSet.SetSize(self.CHAT_WINDOW_WIDTH, 25)
		else:
			chatInputSet.SetSize(550, 25)
		self.chatInputSet = chatInputSet

		if app.ENABLE_EMOTICONS_SYSTEM:
			btnEmoticonsOpen = ui.Button()
			btnEmoticonsOpen.SetParent(self)
			btnEmoticonsOpen.SetUpVisual("d:/ymir work/ui/game/emoji/emoticons/gui/open_norm.png")
			btnEmoticonsOpen.SetOverVisual("d:/ymir work/ui/game/emoji/emoticons/gui/open_over.png")
			btnEmoticonsOpen.SetDownVisual("d:/ymir work/ui/game/emoji/emoticons/gui/open_down.png")
			if app.ENABLE_CHAT_TABS:
				btnEmoticonsOpen.SetUpVisual("d:/ymir work/ui/game/taskbar/clr_emoji_btn_1.tga")
				btnEmoticonsOpen.SetOverVisual("d:/ymir work/ui/game/taskbar/clr_emoji_btn_2.tga")
				btnEmoticonsOpen.SetDownVisual("d:/ymir work/ui/game/taskbar/clr_emoji_btn_2.tga")
			else:
				btnEmoticonsOpen.SetButtonScale(0.29, 0.29)
			btnEmoticonsOpen.SetPosition(51, 2)
			if app.ENABLE_CHAT_TABS:
				btnEmoticonsOpen.SAFE_SetEvent(self.OpenEmojiPicker)
			else:
				btnEmoticonsOpen.SAFE_SetEvent(self.OpenEmoticons)
			btnEmoticonsOpen.Hide()
			self.btnEmoticonsOpen = btnEmoticonsOpen

			toolTipEx = ui.Ballon()
			toolTipEx.SetParent(self.btnEmoticonsOpen)
			toolTipEx.SetPosition(0, -38)
			toolTipEx.SetWindowHorizontalAlignCenter()
			toolTipEx.Hide()
			toolTipEx.SetText(localeInfo.TOOLTIP_EMOJI_OPEN)
			self.toolTipEx = toolTipEx
			self.btnEmoticonsOpen.SetToolTipWindow(self.toolTipEx)

			btnEmoticonsClose = ui.Button()
			btnEmoticonsClose.SetParent(self)
			btnEmoticonsClose.SetUpVisual("d:/ymir work/ui/game/emoji/emoticons/gui/close_norm.png")
			btnEmoticonsClose.SetOverVisual("d:/ymir work/ui/game/emoji/emoticons/gui/close_over.png")
			btnEmoticonsClose.SetDownVisual("d:/ymir work/ui/game/emoji/emoticons/gui/close_down.png")
			if app.ENABLE_CHAT_TABS:
				btnEmoticonsClose.SetUpVisual("d:/ymir work/ui/game/taskbar/clr_emoji_btn_2.tga")
				btnEmoticonsClose.SetOverVisual("d:/ymir work/ui/game/taskbar/clr_emoji_btn_2.tga")
				btnEmoticonsClose.SetDownVisual("d:/ymir work/ui/game/taskbar/clr_emoji_btn_1.tga")
			else:
				btnEmoticonsClose.SetButtonScale(0.29, 0.29)
			btnEmoticonsClose.SetToolTipText(localeInfo.TOOLTIP_EMOJI_OPEN)
			btnEmoticonsClose.SetPosition(51, 2 + 250)
			btnEmoticonsClose.SAFE_SetEvent(self.CloseEmoticons)
			btnEmoticonsClose.Hide()
			self.btnEmoticonsClose = btnEmoticonsClose

			toolTipEr = ui.Ballon()
			toolTipEr.SetParent(self.btnEmoticonsClose)
			toolTipEr.SetPosition(0, -38)
			toolTipEr.SetWindowHorizontalAlignCenter()
			toolTipEr.Hide()
			toolTipEr.SetText(localeInfo.TOOLTIP_EMOJI_CLOSE)
			self.toolTipEr = toolTipEr
			self.btnEmoticonsClose.SetToolTipWindow(self.toolTipEr)

		btnSendWhisper = ui.Button()
		btnSendWhisper.SetParent(self)
		btnSendWhisper.SetUpVisual("d:/ymir work/ui/game/taskbar/Send_Whisper_Button_01.sub")
		btnSendWhisper.SetOverVisual("d:/ymir work/ui/game/taskbar/Send_Whisper_Button_02.sub")
		btnSendWhisper.SetDownVisual("d:/ymir work/ui/game/taskbar/Send_Whisper_Button_03.sub")
		if app.ENABLE_EMOTICONS_SYSTEM:
			toolTipSendWhisper = ui.Ballon()
			toolTipSendWhisper.SetParent(self)
			toolTipSendWhisper.SetPosition(0, -38)
			toolTipSendWhisper.SetWindowHorizontalAlignCenter()
			toolTipSendWhisper.Hide()
			toolTipSendWhisper.SetText(localeInfo.CHAT_SEND_MEMO)
			self.toolTipSendWhisper = toolTipSendWhisper
			btnSendWhisper.SetToolTipWindow(self.toolTipSendWhisper)
		else:
			btnSendWhisper.SetToolTipText(localeInfo.CHAT_SEND_MEMO)
		btnSendWhisper.Hide()
		self.btnSendWhisper = btnSendWhisper

		if app.ENABLE_AUTO_CHAT:
			btnAutoChat = ui.Button()
			btnAutoChat.SetParent(self)
			btnAutoChat.SetUpVisual("d:/ymir work/ui/game/taskbar/auto_chat_norm.png")
			btnAutoChat.SetOverVisual("d:/ymir work/ui/game/taskbar/auto_chat_hover.png")
			btnAutoChat.SetDownVisual("d:/ymir work/ui/game/taskbar/auto_chat_select.png")
			btnAutoChat.SAFE_SetEvent(self.ToggleAutoChat)
			if app.ENABLE_EMOTICONS_SYSTEM:
				toolTipAutoChat = ui.Ballon()
				toolTipAutoChat.SetParent(self)
				toolTipAutoChat.SetPosition(0, -38)
				toolTipAutoChat.SetWindowHorizontalAlignCenter()
				toolTipAutoChat.Hide()
				toolTipAutoChat.SetText(localeInfo.AUTO_CHAT_TITLE)
				self.toolTipAutoChat = toolTipAutoChat
				btnAutoChat.SetToolTipWindow(self.toolTipAutoChat)
			else:
				btnAutoChat.SetToolTipText(localeInfo.AUTO_CHAT_TITLE)
			btnAutoChat.Hide()
			self.btnAutoChat = btnAutoChat

		btnChatLog = ui.Button()
		btnChatLog.SetParent(self)
		btnChatLog.SetUpVisual("d:/ymir work/ui/game/taskbar/Open_Chat_Log_Button_01.sub")
		btnChatLog.SetOverVisual("d:/ymir work/ui/game/taskbar/Open_Chat_Log_Button_02.sub")
		btnChatLog.SetDownVisual("d:/ymir work/ui/game/taskbar/Open_Chat_Log_Button_03.sub")
		if app.ENABLE_EMOTICONS_SYSTEM:
			toolTipChatLog = ui.Ballon()
			toolTipChatLog.SetParent(self)
			toolTipChatLog.SetPosition(0, -38)
			toolTipChatLog.SetWindowHorizontalAlignCenter()
			toolTipChatLog.Hide()
			toolTipChatLog.SetText(localeInfo.CHAT_LOG)
			self.toolTipChatLog = toolTipChatLog
			btnChatLog.SetToolTipWindow(self.toolTipChatLog)
		else:
			btnChatLog.SetToolTipText(localeInfo.CHAT_LOG)
		btnChatLog.Hide()
		self.btnChatLog = btnChatLog

		btnChatSizing = self.ChatButton()
		btnChatSizing.SetOwner(self)
		btnChatSizing.SetMoveEvent(ui.__mem_func__(self.Refresh))
		btnChatSizing.Hide()
		self.btnChatSizing = btnChatSizing

		imgChatBarLeft = ui.ImageBox()
		imgChatBarLeft.SetParent(self.btnChatSizing)
		imgChatBarLeft.AddFlag("not_pick")
		imgChatBarLeft.LoadImage("d:/ymir work/ui/pattern/chat_bar_left.tga")
		imgChatBarLeft.Show()
		self.imgChatBarLeft = imgChatBarLeft
		imgChatBarRight = ui.ImageBox()
		imgChatBarRight.SetParent(self.btnChatSizing)
		imgChatBarRight.AddFlag("not_pick")
		imgChatBarRight.LoadImage("d:/ymir work/ui/pattern/chat_bar_right.tga")
		imgChatBarRight.Show()
		self.imgChatBarRight = imgChatBarRight
		imgChatBarMiddle = ui.ExpandedImageBox()
		imgChatBarMiddle.SetParent(self.btnChatSizing)
		imgChatBarMiddle.AddFlag("not_pick")
		imgChatBarMiddle.LoadImage("d:/ymir work/ui/pattern/chat_bar_middle.tga")
		imgChatBarMiddle.Show()
		self.imgChatBarMiddle = imgChatBarMiddle

		self.interface = None
		if app.ENABLE_CHAT_TABS:
			self.__CreateChatTabs()

		scrollBar = ui.ScrollBar()
		scrollBar.AddFlag("float")
		scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollBar = scrollBar

		self.Refresh()
		self.chatInputSet.RefreshPosition()

	def __del__(self):
		ui.Window.__del__(self)

	def __RegisterChatColorDict(self):
		CHAT_COLOR_DICT = {
			chat.CHAT_TYPE_TALKING : colorInfo.CHAT_RGB_TALK,
			chat.CHAT_TYPE_INFO : colorInfo.CHAT_RGB_INFO,
			chat.CHAT_TYPE_NOTICE : colorInfo.CHAT_RGB_NOTICE,
			chat.CHAT_TYPE_PARTY : colorInfo.CHAT_RGB_PARTY,
			chat.CHAT_TYPE_GUILD : colorInfo.CHAT_RGB_GUILD,
			chat.CHAT_TYPE_COMMAND : colorInfo.CHAT_RGB_COMMAND,
			chat.CHAT_TYPE_SHOUT : colorInfo.CHAT_RGB_SHOUT,
			chat.CHAT_TYPE_WHISPER : colorInfo.CHAT_RGB_WHISPER,
			chat.CHAT_TYPE_BIG_NOTICE : colorInfo.CHAT_RGB_BIG_NOTICE,
		}

		if app.ENABLE_DICE_SYSTEM:
			CHAT_COLOR_DICT.update({chat.CHAT_TYPE_DICE_INFO : colorInfo.CHAT_RGB_DICE_INFO,})

		if app.ENABLE_CHAT_TABS:
			CHAT_COLOR_DICT.update({
				chat.CHAT_TYPE_DUNGEON : colorInfo.CHAT_RGB_NOTICE,
				chat.CHAT_TYPE_EXCHANGE : colorInfo.CHAT_RGB_INFO,
				chat.CHAT_TYPE_DROP : colorInfo.CHAT_RGB_INFO,
			})

		for colorItem in CHAT_COLOR_DICT.items():
			type=colorItem[0]
			rgb=colorItem[1]
			chat.SetChatColor(type, rgb[0], rgb[1], rgb[2])

	def Destroy(self):
		self.chatInputSet.Destroy()
		self.chatInputSet = None

		self.btnSendWhisper = 0
		self.btnChatLog = 0
		self.btnChatSizing = 0

		if app.ENABLE_EMOTICONS_SYSTEM:
			self.emoticonsBoard.Destroy()
			self.emoticonsBoard = None
			self.btnEmoticonsOpen = None
			self.btnEmoticonsClose = None

	if app.ENABLE_EMOTICONS_SYSTEM:
		def OpenEmoticons(self):
			self.LINE_HEIGHT = 250

			self.btnEmoticonsOpen.Hide()
			self.btnEmoticonsClose.Show()
			self.emoticonsBoard.Open(self.chatInputSet.chatLine)

			self.SetSize(self.CHAT_WINDOW_WIDTH, self.EDIT_LINE_HEIGHT + 250)
			(x, y, width, height) = self.GetRect()
			self.SetPosition(x, y - 250)
			self.SetHeight(self.GetHeight() + 220)

			self.chatInputSet.SetPosition(0, 250)
			self.btnSendWhisper.SetPosition(self.GetWidth() - 50, 2 + self.LINE_HEIGHT)
			self.btnChatLog.SetPosition(self.GetWidth() - 25, 2 + self.LINE_HEIGHT)
			if app.ENABLE_CHAT_TABS:
				self.__PlaceInputButtons()
			self.Refresh()

		def CloseEmoticons(self):
			self.LINE_HEIGHT = 0

			self.btnEmoticonsOpen.Show()
			self.btnEmoticonsClose.Hide()
			self.emoticonsBoard.Close()

			self.SetSize(self.CHAT_WINDOW_WIDTH, self.EDIT_LINE_HEIGHT)
			(x, y, width, height) = self.GetRect()
			self.SetPosition(x, y + 250)
			self.SetHeight(224)

			self.chatInputSet.SetPosition(0, 0)
			self.btnSendWhisper.SetPosition(self.GetWidth() - 50, 2 + self.LINE_HEIGHT)
			self.btnChatLog.SetPosition(self.GetWidth() - 25, 2 + self.LINE_HEIGHT)
			if app.ENABLE_CHAT_TABS:
				self.__PlaceInputButtons()
			self.Refresh()

	def OpenChat(self):
		if app.ENABLE_EMOTICONS_SYSTEM:
			self.SetSize(self.CHAT_WINDOW_WIDTH, self.EDIT_LINE_HEIGHT + self.LINE_HEIGHT)
		else:
			self.SetSize(self.CHAT_WINDOW_WIDTH, self.EDIT_LINE_HEIGHT)
		chat.SetBoardState(self.chatID, chat.BOARD_STATE_EDIT)
		self.boardState = chat.BOARD_STATE_EDIT

		(x, y, width, height) = self.GetRect()
		(btnX, btnY) = self.btnChatSizing.GetGlobalPosition()

		chat.SetPosition(self.chatID, x + 10, y)
		if app.ENABLE_EMOTICONS_SYSTEM:
			chat.SetHeight(self.chatID, y - btnY - (self.EDIT_LINE_HEIGHT + self.LINE_HEIGHT) + 100 - 25)
		else:
			chat.SetHeight(self.chatID, y - btnY - self.EDIT_LINE_HEIGHT + 100)

		if self.IsShow():
			self.btnChatSizing.Show()

		self.Refresh()

		if app.ENABLE_EMOTICONS_SYSTEM:
			self.btnSendWhisper.SetPosition(self.GetWidth() - 50, 2 + self.LINE_HEIGHT)
		else:
			self.btnSendWhisper.SetPosition(self.GetWidth() - 50, 2)
		self.btnSendWhisper.Show()

		if app.ENABLE_EMOTICONS_SYSTEM:
			self.btnChatLog.SetPosition(self.GetWidth() - 25, 2 + self.LINE_HEIGHT)
		else:
			self.btnChatLog.SetPosition(self.GetWidth() - 25, 2)
		self.btnChatLog.Show()

		if app.ENABLE_EMOTICONS_SYSTEM:
			if self.LINE_HEIGHT > 0:
				self.emoticonsBoard.Open(self.chatInputSet.chatLine)
				self.btnEmoticonsOpen.Hide()
				self.btnEmoticonsClose.Show()
			else:
				self.emoticonsBoard.Close()
				self.btnEmoticonsClose.Hide()
				self.btnEmoticonsOpen.Show()

		self.chatInputSet.Open()
		self.chatInputSet.SetTop()
		self.SetTop()
		if app.ENABLE_CHAT_TABS:
			self.__PlaceInputButtons()
			self.__RefreshStopChat()

	def CloseChat(self):
		chat.SetBoardState(self.chatID, chat.BOARD_STATE_VIEW)
		self.boardState = chat.BOARD_STATE_VIEW

		(x, y, width, height) = self.GetRect()

		if app.ENABLE_EMOTICONS_SYSTEM:
			if self.LINE_HEIGHT > 0:
				self.LINE_HEIGHT = 0

				self.SetPosition(x, y + 250)
				self.SetHeight(224)

				self.chatInputSet.SetPosition(0, 0)
				self.btnSendWhisper.SetPosition(self.GetWidth() - 50, 2 + self.LINE_HEIGHT)
				self.btnChatLog.SetPosition(self.GetWidth() - 25, 2 + self.LINE_HEIGHT)
				self.Refresh()

			chat.SetPosition(self.chatID, x + 10, y + (self.EDIT_LINE_HEIGHT + self.LINE_HEIGHT))
			chat.Close()
		else:
			chat.SetPosition(self.chatID, x + 10, y + self.EDIT_LINE_HEIGHT)

		self.SetSize(self.CHAT_WINDOW_WIDTH, 0)

		self.chatInputSet.Close()
		self.btnSendWhisper.Hide()
		self.btnChatLog.Hide()
		self.btnChatSizing.Hide()
		if app.ENABLE_AUTO_CHAT and self.btnAutoChat:
			self.btnAutoChat.Hide()
		if app.ENABLE_CHAT_TABS and self.emojiPicker:
			self.emojiPicker.Hide()

		if app.ENABLE_EMOTICONS_SYSTEM:
			self.emoticonsBoard.Close()
			self.btnEmoticonsOpen.Hide()
			self.btnEmoticonsClose.Hide()

		self.Refresh()

	def SetSendWhisperEvent(self, event):
		self.btnSendWhisper.SetEvent(event)

	def SetOpenChatLogEvent(self, event):
		self.btnChatLog.SetEvent(event)

	def IsEditMode(self):
		if chat.BOARD_STATE_EDIT == self.boardState:
			return TRUE

		return FALSE

	def __RefreshSizingBar(self):
		(x, y, width, height) = self.GetRect()
		gxChat, gyChat = self.btnChatSizing.GetGlobalPosition()
		self.btnChatSizing.SetPosition(x, gyChat)
		self.btnChatSizing.SetSize(width, 22)
		self.imgChatBarLeft.SetPosition(0, 0)
		self.imgChatBarRight.SetPosition(width - 64, 0)
		self.imgChatBarMiddle.SetPosition(64, 0)
		self.imgChatBarMiddle.SetRenderingRect(0.0, 0.0, float(width - 128) / 64.0 - 1.0, 0.0)
		if app.ENABLE_CHAT_TABS and self.chatTabLine:
			self.__RefreshChatTabLine(width)

	def SetPosition(self, x, y):
		ui.Window.SetPosition(self, x, y)
		self.__RefreshSizingBar()

	def SetSize(self, width, height):
		ui.Window.SetSize(self, width, height)
		self.__RefreshSizingBar()

	def SetHeight(self, height):
		gxChat, gyChat = self.btnChatSizing.GetGlobalPosition()
		self.btnChatSizing.SetPosition(gxChat, wndMgr.GetScreenHeight() - height)

	def Refresh(self):
		if self.boardState == chat.BOARD_STATE_EDIT:
			self.RefreshBoardEditState()
		elif self.boardState == chat.BOARD_STATE_VIEW:
			self.RefreshBoardViewState()

	def RefreshBoardEditState(self):
		(x, y, width, height) = self.GetRect()
		(btnX, btnY) = self.btnChatSizing.GetGlobalPosition()

		self.xBar = x
		self.yBar = btnY
		self.widthBar = width
		if app.ENABLE_EMOTICONS_SYSTEM:
			self.heightBar = y - btnY + (self.EDIT_LINE_HEIGHT + self.LINE_HEIGHT)
		else:
			self.heightBar = y - btnY + self.EDIT_LINE_HEIGHT
		self.curHeightBar = self.heightBar

		chat.SetPosition(self.chatID, x + 10, y)
		chat.SetHeight(self.chatID, y - btnY - self.EDIT_LINE_HEIGHT)
		chat.ArrangeShowingChat(self.chatID)

		if btnY > y:
			self.btnChatSizing.SetPosition(btnX, y)
			if app.ENABLE_EMOTICONS_SYSTEM:
				self.heightBar = (self.EDIT_LINE_HEIGHT + self.LINE_HEIGHT)
			else:
				self.heightBar = self.EDIT_LINE_HEIGHT

		self.__RefreshTaskBarPosition()

	def RefreshBoardViewState(self):
		(x, y, width, height) = self.GetRect()
		(btnX, btnY) = self.btnChatSizing.GetGlobalPosition()
		textAreaHeight = self.visibleLineCount * chat.GetLineStep(self.chatID)

		chat.SetPosition(self.chatID, x + 10, y + self.EDIT_LINE_HEIGHT)
		chat.SetHeight(self.chatID, y - btnY - self.EDIT_LINE_HEIGHT + 100)

		if self.boardState == chat.BOARD_STATE_EDIT:
			textAreaHeight += 45
		elif self.visibleLineCount != 0:
			textAreaHeight += 10 + 10

		self.xBar = x
		if app.ENABLE_EMOTICONS_SYSTEM:
			self.yBar = y + (self.EDIT_LINE_HEIGHT + self.LINE_HEIGHT) - textAreaHeight
		else:
			self.yBar = y + self.EDIT_LINE_HEIGHT - textAreaHeight
		self.widthBar = width
		self.heightBar = textAreaHeight

		self.scrollBar.Hide()
		self.__RefreshTaskBarPosition()

	def OnUpdate(self):
		if app.ENABLE_AUTO_CHAT and self.interface and self.interface.wndAutoChat:
			self.interface.wndAutoChat.Tick()
		if app.ENABLE_CHAT_TABS:
			self.__UpdateStopChat()
		if self.boardState == chat.BOARD_STATE_EDIT:
			chat.Update(self.chatID)
		elif self.boardState == chat.BOARD_STATE_VIEW:
			if systemSetting.IsViewChat():
				chat.Update(self.chatID)

	def OnRender(self):
		if chat.GetVisibleLineCount(self.chatID) != self.visibleLineCount:
			self.visibleLineCount = chat.GetVisibleLineCount(self.chatID)
			self.Refresh()

		if self.curHeightBar != self.heightBar:
			self.curHeightBar += (self.heightBar - self.curHeightBar) / 10

		if self.boardState == chat.BOARD_STATE_EDIT:
			grp.SetColor(self.BOARD_MIDDLE_COLOR)
			if app.ENABLE_CHAT_TABS:
				top = self.CHAT_TAB_LINE_Y + 2
				grp.RenderBar(self.xBar, self.yBar + (self.heightBar - self.curHeightBar) + top, self.widthBar, max(0, self.curHeightBar + 10 - top))
			else:
				grp.RenderBar(self.xBar, self.yBar + (self.heightBar - self.curHeightBar) + 10, self.widthBar, self.curHeightBar)
			chat.Render(self.chatID)
		elif self.boardState == chat.BOARD_STATE_VIEW:
			if systemSetting.IsViewChat():
				grp.RenderGradationBar(self.xBar, self.yBar + (self.heightBar - self.curHeightBar), self.widthBar, self.curHeightBar, self.BOARD_START_COLOR, self.BOARD_END_COLOR)
				chat.Render(self.chatID)

	##########
	## Event
	def OnTop(self):
		self.btnChatSizing.SetTop()
		self.scrollBar.SetTop()

	def OnScroll(self):
		if not self.scrollLock:
			self.scrollBarPos = self.scrollBar.GetPos()

		lineCount = chat.GetLineCount(self.chatID)
		visibleLineCount = chat.GetVisibleLineCount(self.chatID)
		endLine = visibleLineCount + int(float(lineCount - visibleLineCount) * self.scrollBarPos)

		chat.SetEndPos(self.chatID, self.scrollBarPos)

	def OnChangeChatMode(self):
		self.chatInputSet.OnChangeChatMode()

	def SetChatFocus(self):
		self.chatInputSet.SetChatFocus()

	def BindInterface(self, interface):
		self.interface = interface
		self.chatInputSet.BindInterface(interface)

	if app.ENABLE_CHAT_TABS:
		CHAT_TAB_PATH = "d:/ymir work/ui/chat/"
		CHAT_TAB_X = 4
		CHAT_TAB_TEXT_Y = 8			# tab label centre (the engine centres text ~3 px low)
		CHAT_TAB_WIDTH = 57
		CHAT_TAB_LINE_Y = 18
		CHAT_TAB_OPEN_LEFT = 2
		CHAT_TAB_OPEN_RIGHT = 52		# ... to x=52
		CHAT_TAB_RIGHT_CORNER = (
			(4, 18, 4, 2, grp.GenerateColor(216 / 255.0, 202 / 255.0, 189 / 255.0, 1.0)),
			(2, 20, 2, 3, grp.GenerateColor(216 / 255.0, 202 / 255.0, 189 / 255.0, 1.0)),
			(1, 23, 1, 6, grp.GenerateColor(208 / 255.0, 194 / 255.0, 182 / 255.0, 0.96)),
			(2, 23, 1, 6, grp.GenerateColor(105 / 255.0, 99 / 255.0, 96 / 255.0, 0.91)),
		)

		STOP_KEY_WIDTH = 40
		STOP_KEY_HEIGHT = 16
		STOP_KEY_RIGHT = 117
		STOP_KEY_TEXT_COLOR = 0xffd2c6b6
		STOP_KEY_PARTS = (
			(0, 0, 40, 16, 0xff46413c),
			(1, 1, 38, 14, 0xff060100),
			(2, 2, 36, 3, 0xff41362b),
			(2, 5, 36, 3, 0xff3d3227),
			(2, 8, 36, 2, 0xff302820),
			(2, 10, 36, 2, 0xff25201b),
			(2, 12, 36, 2, 0xff1d1915),
		)

		## tab tooltip "[Ctrl] - Coklu secim icin basili tut": 200x39 board, key box 38x14 at (20, 13), text at x=61
		TAB_TOOLTIP_WIDTH = 200
		TAB_TOOLTIP_HEIGHT = 39
		TAB_TOOLTIP_GAP = 15			# tooltip bottom -> tab top
		TAB_TOOLTIP_X = -18
		TAB_TOOLTIP_KEY_X = 20
		TAB_TOOLTIP_KEY_Y = 13
		TAB_TOOLTIP_TEXT_X = 61
		CTRL_KEY_PARTS = (
			(0, 0, 38, 14, 0xff46413c),
			(1, 1, 36, 12, 0xff060100),
			(2, 2, 34, 3, 0xff41362b),
			(2, 5, 34, 2, 0xff3d3227),
			(2, 7, 34, 2, 0xff302820),
			(2, 9, 34, 2, 0xff25201b),
			(2, 11, 34, 2, 0xff1d1915),
		)

		def __CreateTabToolTip(self):
			board = ui.ThinBoard("TOP_MOST")
			board.AddFlag("float")
			board.AddFlag("not_pick")
			board.SetSize(self.TAB_TOOLTIP_WIDTH, self.TAB_TOOLTIP_HEIGHT)
			board.Hide()

			key = ui.Window()
			key.SetParent(board)
			key.AddFlag("not_pick")
			key.SetPosition(self.TAB_TOOLTIP_KEY_X, self.TAB_TOOLTIP_KEY_Y)
			key.SetSize(38, 14)
			key.Show()
			parts = []
			for (px, py, pw, ph, color) in self.CTRL_KEY_PARTS:
				part = ui.Bar()
				part.SetParent(key)
				part.AddFlag("not_pick")
				part.SetPosition(px, py)
				part.SetSize(pw, ph)
				part.SetColor(color)
				part.Show()
				parts.append(part)

			keyText = ui.TextLine()
			keyText.SetParent(key)
			keyText.SetPosition(19, 4)
			keyText.SetHorizontalAlignCenter()
			keyText.SetVerticalAlignCenter()
			keyText.SetPackedFontColor(self.STOP_KEY_TEXT_COLOR)
			keyText.SetText(localeInfo.AUTO_CTRL)
			keyText.Show()

			text = ui.TextLine()
			text.SetParent(board)
			text.SetPosition(self.TAB_TOOLTIP_TEXT_X, self.TAB_TOOLTIP_HEIGHT / 2 - 1)
			text.SetVerticalAlignCenter()
			text.SetText(localeInfo.CHAT_TAB_MULTI_SELECT)
			text.Show()

			self.tabToolTip = board
			self.tabToolTipParts = (key, parts, keyText, text)

		def __ShowTabToolTip(self, idx):
			if not self.tabToolTip:
				return
			(bx, by) = self.chatTabs[idx].GetGlobalPosition()
			self.tabToolTip.SetPosition(bx + self.TAB_TOOLTIP_X, by - self.TAB_TOOLTIP_GAP - self.TAB_TOOLTIP_HEIGHT)
			self.tabToolTip.Show()
			self.tabToolTip.SetTop()

		def __HideTabToolTip(self):
			if self.tabToolTip:
				self.tabToolTip.Hide()

		def __RefreshStopChat(self):
			if not self.stopChatText:
				return
			(x, y, width, height) = self.GetRect()
			self.stopKeyBox.SetPosition(width - self.STOP_KEY_RIGHT, -1)
			self.stopChatText.SetPosition(width - self.STOP_KEY_RIGHT + self.STOP_KEY_WIDTH + 4, -1)
			if self.chatStopped:
				self.stopChatText.SetText(localeInfo.CHAT_TAB_START_CHAT)
			else:
				self.stopChatText.SetText(localeInfo.CHAT_TAB_STOP_CHAT)

		def ToggleStopChat(self):
			self.chatStopped = not self.chatStopped
			if self.chatStopped:
				self.chatStopLineCount = chat.GetLineCount(self.chatID)
				self.chatStopLastCount = self.chatStopLineCount
			else:
				self.scrollBarPos = 1.0
				chat.SetEndPos(self.chatID, 1.0)
			self.__RefreshStopChat()

		def __UpdateStopChat(self):
			if not self.chatStopped:
				return
			lineCount = chat.GetLineCount(self.chatID)
			if lineCount == self.chatStopLastCount:
				return
			self.chatStopLastCount = lineCount
			visible = chat.GetVisibleLineCount(self.chatID)
			if lineCount - visible - 1 <= 0:
				return
			pos = float(self.chatStopLineCount - 1 - visible) / float(lineCount - visible - 1)
			chat.SetEndPos(self.chatID, max(0.0, min(1.0, pos)))

		def __PlaceInputButtons(self):
			lineHeight = 0
			if app.ENABLE_EMOTICONS_SYSTEM:
				lineHeight = self.LINE_HEIGHT
				self.btnEmoticonsOpen.SetPosition(self.GetWidth() - 100, 2 + lineHeight)
				self.btnEmoticonsClose.SetPosition(self.GetWidth() - 100, 2 + lineHeight)
			if app.ENABLE_AUTO_CHAT and self.btnAutoChat:
				self.btnAutoChat.SetPosition(self.GetWidth() - 75, 2 + lineHeight)
				self.btnAutoChat.Show()
			self.btnSendWhisper.SetPosition(self.GetWidth() - 50, 2 + lineHeight)
			self.btnChatLog.SetPosition(self.GetWidth() - 25, 2 + lineHeight)

		def __GetChatTabList(self):
			infoTypes = [chat.CHAT_TYPE_INFO, chat.CHAT_TYPE_NOTICE, chat.CHAT_TYPE_BIG_NOTICE]
			if app.ENABLE_DICE_SYSTEM:
				infoTypes.append(chat.CHAT_TYPE_DICE_INFO)
			return (
				(localeInfo.CHAT_TAB_ALL, None),
				(localeInfo.CHAT_TAB_NORMAL, (chat.CHAT_TYPE_TALKING, chat.CHAT_TYPE_PARTY)),
				(localeInfo.CHAT_TAB_GUILD, (chat.CHAT_TYPE_GUILD,)),
				(localeInfo.CHAT_TAB_GENERAL, (chat.CHAT_TYPE_SHOUT,)),
				(localeInfo.CHAT_TAB_EXCHANGE, (chat.CHAT_TYPE_EXCHANGE,)),
				(localeInfo.CHAT_TAB_INFO, tuple(infoTypes)),
				(localeInfo.CHAT_TAB_DROP, (chat.CHAT_TYPE_DROP,)),
				(localeInfo.CHAT_TAB_DUNGEON, (chat.CHAT_TYPE_DUNGEON,)),
			)

		def __CreateChatTabs(self):
			self.imgChatBarLeft.Hide()
			self.imgChatBarRight.Hide()
			self.imgChatBarMiddle.Hide()

			line = ui.ExpandedImageBox()
			line.SetParent(self.btnChatSizing)
			line.AddFlag("not_pick")
			line.LoadImage(self.CHAT_TAB_PATH + "chatmenutab_line.tga")
			line.Show()
			self.chatTabLine = line

			lineRight = ui.ExpandedImageBox()
			lineRight.SetParent(self.btnChatSizing)
			lineRight.AddFlag("not_pick")
			lineRight.LoadImage(self.CHAT_TAB_PATH + "chatmenutab_line.tga")
			lineRight.Show()
			self.chatTabLineRight = lineRight

			cornerLeft = ui.ImageBox()
			cornerLeft.SetParent(self.btnChatSizing)
			cornerLeft.AddFlag("not_pick")
			cornerLeft.LoadImage(self.CHAT_TAB_PATH + "chat_linebar_left.tga")
			cornerLeft.SetPosition(0, self.CHAT_TAB_LINE_Y - 1)
			cornerLeft.Show()
			self.chatTabCornerLeft = cornerLeft

			self.chatTabCornerRight = []
			for (cx, cy, cw, ch, color) in self.CHAT_TAB_RIGHT_CORNER:
				bar = ui.Bar()
				bar.SetParent(self.btnChatSizing)
				bar.AddFlag("not_pick")
				bar.SetSize(cw, ch)
				bar.SetColor(color)
				bar.Show()
				self.chatTabCornerRight.append((bar, cx, cy))

			keyBox = ui.Window()
			keyBox.SetParent(self.btnChatSizing)
			keyBox.AddFlag("not_pick")
			keyBox.SetSize(self.STOP_KEY_WIDTH, self.STOP_KEY_HEIGHT)
			keyBox.Show()
			self.stopKeyBox = keyBox

			self.stopKeyParts = []
			for (px, py, pw, ph, color) in self.STOP_KEY_PARTS:
				part = ui.Bar()
				part.SetParent(keyBox)
				part.AddFlag("not_pick")
				part.SetPosition(px, py)
				part.SetSize(pw, ph)
				part.SetColor(color)
				part.Show()
				self.stopKeyParts.append(part)

			keyText = ui.TextLine()
			keyText.SetParent(keyBox)
			keyText.SetPosition(self.STOP_KEY_WIDTH / 2, self.STOP_KEY_HEIGHT / 2)
			keyText.SetHorizontalAlignCenter()
			keyText.SetVerticalAlignCenter()
			keyText.SetPackedFontColor(self.STOP_KEY_TEXT_COLOR)
			keyText.SetText(localeInfo.AUTO_TAB)
			keyText.Show()
			self.stopKeyText = keyText

			stopText = ui.TextLine()
			stopText.SetParent(self.btnChatSizing)
			stopText.SetOutline()
			stopText.Show()
			self.stopChatText = stopText

			self.chatStopped = False
			self.chatStopLineCount = 0
			self.chatStopLastCount = 0
			self.__RefreshStopChat()

			self.chatTabList = self.__GetChatTabList()
			self.chatTabs = []
			for idx in xrange(len(self.chatTabList)):
				btn = ui.Button()
				btn.SetParent(self.btnChatSizing)
				btn.SetPosition(self.CHAT_TAB_X + idx * self.CHAT_TAB_WIDTH, 0)
				btn.SetEvent(ui.__mem_func__(self.OnChatTabClicked), idx)
				btn.SetShowToolTipEvent(ui.__mem_func__(self.__ShowTabToolTip), idx)
				btn.SetHideToolTipEvent(ui.__mem_func__(self.__HideTabToolTip))
				btn.Show()
				self.chatTabs.append(btn)

			self.__CreateTabToolTip()
			self.chatTabSelected = [0]
			self.chatTabIndex = 0
			self.__RefreshChatTabs()

		def __RefreshChatTabLine(self, width):
			if not self.chatTabLineRight:
				return
			selected = sorted(self.chatTabSelected)
			pieces = []
			start = 0
			for idx in selected:
				tabX = self.CHAT_TAB_X + idx * self.CHAT_TAB_WIDTH
				pieces.append((start, tabX + self.CHAT_TAB_OPEN_LEFT))
				start = tabX + self.CHAT_TAB_OPEN_RIGHT
			pieces.append((start, width))

			segments = [self.chatTabLine, self.chatTabLineRight] + self.chatTabLineExtra
			while len(segments) < len(pieces):
				seg = ui.ExpandedImageBox()
				seg.SetParent(self.btnChatSizing)
				seg.AddFlag("not_pick")
				seg.LoadImage(self.CHAT_TAB_PATH + "chatmenutab_line.tga")
				segments.append(seg)
				self.chatTabLineExtra = self.chatTabLineExtra + [seg]

			for i in xrange(len(segments)):
				seg = segments[i]
				if i < len(pieces) and pieces[i][1] > pieces[i][0]:
					(x0, x1) = pieces[i]
					seg.SetPosition(x0, 0)
					seg.SetRenderingRect(0.0, 0.0, float(x1 - x0) / float(self.CHAT_TAB_WIDTH) - 1.0, 0.0)
					seg.Show()
				else:
					seg.Hide()

			for (bar, cx, cy) in self.chatTabCornerRight:
				bar.SetPosition(width - cx, cy)

		def __RefreshChatTabs(self):
			selected = self.chatTabSelected
			for idx in xrange(len(self.chatTabs)):
				btn = self.chatTabs[idx]
				if idx in selected:
					image = self.CHAT_TAB_PATH + "chatmenutab_down.tga"
					btn.SetUpVisual(image)
					btn.SetOverVisual(image)
					btn.SetDownVisual(image)
				else:
					btn.SetUpVisual(self.CHAT_TAB_PATH + "chatmenutab_default.tga")
					btn.SetOverVisual(self.CHAT_TAB_PATH + "chatmenutab_drag.tga")
					btn.SetDownVisual(self.CHAT_TAB_PATH + "chatmenutab_down.tga")
				btn.SetText(self.chatTabList[idx][0])
				if btn.ButtonText:
					btn.ButtonText.SetPosition(btn.GetWidth() / 2, self.CHAT_TAB_TEXT_Y)

		def __GetAllChatTypes(self):
			return [chat.CHAT_TYPE_TALKING, chat.CHAT_TYPE_INFO, chat.CHAT_TYPE_NOTICE, chat.CHAT_TYPE_PARTY, chat.CHAT_TYPE_GUILD,
				chat.CHAT_TYPE_COMMAND, chat.CHAT_TYPE_SHOUT, chat.CHAT_TYPE_WHISPER, chat.CHAT_TYPE_BIG_NOTICE, chat.CHAT_TYPE_DICE_INFO,
				chat.CHAT_TYPE_CONTROL_NOTICE, chat.CHAT_TYPE_MISSION, chat.CHAT_TYPE_DUNGEON, chat.CHAT_TYPE_EXCHANGE, chat.CHAT_TYPE_DROP]

		def OnChatTabClicked(self, idx):
			if idx < 0 or idx >= len(self.chatTabList):
				return

			ctrl = app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL)
			if ctrl and idx != 0:
				selected = [i for i in self.chatTabSelected if i != 0]
				if idx in selected:
					selected.remove(idx)
				else:
					selected.append(idx)
				if not selected:
					selected = [0]
			else:
				selected = [idx]
			self.chatTabSelected = selected
			self.chatTabIndex = idx

			modes = []
			for i in selected:
				if self.chatTabList[i][1] is None:
					modes = None
					break
				modes.extend(self.chatTabList[i][1])

			for chatType in self.__GetAllChatTypes():
				if modes is None or chatType in modes:
					chat.EnableChatMode(self.chatID, chatType)
				else:
					chat.DisableChatMode(self.chatID, chatType)

			chat.SetEndPos(self.chatID, 1.0)
			self.scrollBarPos = 1.0
			chat.ArrangeShowingChat(self.chatID)
			self.__RefreshChatTabs()
			self.__RefreshChatTabLine(self.GetWidth())
			self.Refresh()

	if app.ENABLE_CHAT_TABS:
		def OpenEmojiPicker(self):
			import uiemojipicker
			if not self.emojiPicker:
				self.emojiPicker = uiemojipicker.EmojiSelectorWindow()
			self.emojiPicker.SetChatLine(self.chatInputSet.chatLine)
			(bx, by) = self.btnEmoticonsOpen.GetGlobalPosition()
			self.emojiPicker.Toggle(bx + self.btnEmoticonsOpen.GetWidth() - uiemojipicker.WIDTH, by - uiemojipicker.HEIGHT - 4)

	if app.ENABLE_AUTO_CHAT:
		def ToggleAutoChat(self):
			if self.interface:
				self.interface.ToggleAutoChatWindow()

	def __RefreshTaskBarPosition(self):
		if not self.interface or not self.interface.wndExpandedTaskBar:
			return

		if self.boardState == chat.BOARD_STATE_EDIT:
			(btnX, btnY) = self.btnChatSizing.GetGlobalPosition()
			(x, y, width, height) = self.GetRect()
			self.interface.wndExpandedTaskBar.SetChatTop(btnY, x + width / 2)
		else:
			self.interface.wndExpandedTaskBar.SetChatTop(None)

## ChatLogWindow
class ChatLogWindow(ui.Window):

	BLOCK_WIDTH = 32
	CHAT_MODE_NAME = [ localeInfo.CHAT_NORMAL, localeInfo.CHAT_PARTY, localeInfo.CHAT_GUILD, localeInfo.CHAT_SHOUT, localeInfo.CHAT_INFORMATION, localeInfo.CHAT_NOTICE, ]
	CHAT_MODE_INDEX = [ chat.CHAT_TYPE_TALKING,
						chat.CHAT_TYPE_PARTY,
						chat.CHAT_TYPE_GUILD,
						chat.CHAT_TYPE_SHOUT,
						chat.CHAT_TYPE_INFO,
						chat.CHAT_TYPE_NOTICE, ]

	if app.ENABLE_DICE_SYSTEM:
		CHAT_MODE_NAME.append(localeInfo.CHAT_DICE_INFO)
		CHAT_MODE_INDEX.append(chat.CHAT_TYPE_DICE_INFO)

	CHAT_LOG_WINDOW_MINIMUM_WIDTH = 450
	CHAT_LOG_WINDOW_MINIMUM_HEIGHT = 120

	class ResizeButton(ui.DragButton):

		def __init__(self):
			ui.DragButton.__init__(self)

		def __del__(self):
			ui.DragButton.__del__(self)

		def OnMouseOverIn(self):
			app.SetCursor(app.HVSIZE)

		def OnMouseOverOut(self):
			app.SetCursor(app.NORMAL)

	def __init__(self):

		self.allChatMode = TRUE
		if app.ENABLE_EMOTICONS_SYSTEM:
			self.lineChatLog = None
		else:
			self.chatInputSet = None

		ui.Window.__init__(self)
		self.AddFlag("float")
		self.AddFlag("movable")
		self.SetWindowName("ChatLogWindow")
		if app.ENABLE_EMOTICONS_SYSTEM:
			self.__CreateLine()
		else:
			self.__CreateChatInputSet()
		self.__CreateWindow()
		self.__CreateButton()
		self.__CreateScrollBar()

		self.chatID = chat.CreateChatSet(chat.CHAT_SET_LOG_WINDOW)
		chat.SetBoardState(self.chatID, chat.BOARD_STATE_LOG)

		if app.ENABLE_EMOTICONS_SYSTEM:
			chat.SetStep(self.chatID, 20)
			chat.SetFontNameChat("Tahoma:12")

		for i in self.CHAT_MODE_INDEX:
			chat.EnableChatMode(self.chatID, i)

		self.SetPosition(20, 20)
		self.SetSize(self.CHAT_LOG_WINDOW_MINIMUM_WIDTH, self.CHAT_LOG_WINDOW_MINIMUM_HEIGHT)
		self.btnSizing.SetPosition(self.CHAT_LOG_WINDOW_MINIMUM_WIDTH-self.btnSizing.GetWidth(), self.CHAT_LOG_WINDOW_MINIMUM_HEIGHT-self.btnSizing.GetHeight()+2)

		self.OnResize()

	if app.ENABLE_EMOTICONS_SYSTEM:
		def __CreateLine(self):
			lineChatLog = ui.Line()
			lineChatLog.SetParent(self)
			lineChatLog.SetColor(0xffe6d0a2)
			lineChatLog.SetWindowVerticalAlignBottom()
			lineChatLog.Show()
			self.lineChatLog = lineChatLog
	else:
		def __CreateChatInputSet(self):
			chatInputSet = ChatInputSet()
			chatInputSet.SetParent(self)
			chatInputSet.SetEscapeEvent(ui.__mem_func__(self.Close))
			chatInputSet.SetWindowVerticalAlignBottom()
			chatInputSet.Open()
			self.chatInputSet = chatInputSet

	def __CreateWindow(self):
		imgLeft = ui.ImageBox()
		imgLeft.AddFlag("not_pick")
		imgLeft.SetParent(self)

		imgCenter = ui.ExpandedImageBox()
		imgCenter.AddFlag("not_pick")
		imgCenter.SetParent(self)

		imgRight = ui.ImageBox()
		imgRight.AddFlag("not_pick")
		imgRight.SetParent(self)

		imgLeft.LoadImage("d:/ymir work/ui/pattern/chatlogwindow_titlebar_left.tga")
		imgCenter.LoadImage("d:/ymir work/ui/pattern/chatlogwindow_titlebar_middle.tga")
		imgRight.LoadImage("d:/ymir work/ui/pattern/chatlogwindow_titlebar_right.tga")		

		imgLeft.Show()
		imgCenter.Show()
		imgRight.Show()

		btnClose = ui.Button()
		btnClose.SetParent(self)
		btnClose.SetUpVisual("d:/ymir work/ui/public/close_button_01.sub")
		btnClose.SetOverVisual("d:/ymir work/ui/public/close_button_02.sub")
		btnClose.SetDownVisual("d:/ymir work/ui/public/close_button_03.sub")
		btnClose.SetToolTipText(localeInfo.UI_CLOSE, 0, -23)
		btnClose.SetEvent(ui.__mem_func__(self.Close))
		btnClose.Show()

		btnSizing = self.ResizeButton()
		btnSizing.SetParent(self)
		btnSizing.SetMoveEvent(ui.__mem_func__(self.OnResize))
		btnSizing.SetSize(16, 16)
		btnSizing.Show()

		titleName = ui.TextLine()
		titleName.SetParent(self)
		titleName.SetPosition(20, 6)
		titleName.SetText(localeInfo.CHAT_LOG_TITLE)
		titleName.Show()

		self.imgLeft = imgLeft
		self.imgCenter = imgCenter
		self.imgRight = imgRight
		self.btnClose = btnClose
		self.btnSizing = btnSizing
		self.titleName = titleName

	def __CreateButton(self):
		bx = 13

		btnAll = ui.RadioButton()
		btnAll.SetParent(self)
		btnAll.SetPosition(bx, 24)
		btnAll.SetUpVisual("d:/ymir work/ui/public/xsmall_button_01.sub")
		btnAll.SetOverVisual("d:/ymir work/ui/public/xsmall_button_02.sub")
		btnAll.SetDownVisual("d:/ymir work/ui/public/xsmall_button_03.sub")
		btnAll.SetText(localeInfo.CHAT_ALL)
		btnAll.SetEvent(ui.__mem_func__(self.ToggleAllChatMode))
		btnAll.Down()
		btnAll.Show()
		self.btnAll = btnAll

		x = bx + 48
		i = 0
		self.modeButtonList = []
		for name in self.CHAT_MODE_NAME:
			btn = ui.ToggleButton()
			btn.SetParent(self)
			btn.SetPosition(x, 24)
			btn.SetUpVisual("d:/ymir work/ui/public/xsmall_button_01.sub")
			btn.SetOverVisual("d:/ymir work/ui/public/xsmall_button_02.sub")
			btn.SetDownVisual("d:/ymir work/ui/public/xsmall_button_03.sub")
			btn.SetText(name)
			btn.Show()

			mode = self.CHAT_MODE_INDEX[i]
			btn.SetToggleUpEvent(lambda arg=mode: self.ToggleChatMode(arg))
			btn.SetToggleDownEvent(lambda arg=mode: self.ToggleChatMode(arg))
			self.modeButtonList.append(btn)

			x += 48
			i += 1

	def __CreateScrollBar(self):
		scrollBar = ui.SmallThinScrollBar()
		scrollBar.SetParent(self)
		scrollBar.Show()
		scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollBar = scrollBar
		self.scrollBarPos = 1.0

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.imgLeft = None
		self.imgCenter = None
		self.imgRight = None
		self.btnClose = None
		self.btnSizing = None
		self.modeButtonList = []
		self.scrollBar = None
		if app.ENABLE_EMOTICONS_SYSTEM:
			self.lineChatLog = None
		else:
			self.chatInputSet = None

	def ToggleAllChatMode(self):
		if self.allChatMode:
			return

		self.allChatMode = TRUE

		for i in self.CHAT_MODE_INDEX:
			chat.EnableChatMode(self.chatID, i)
		for btn in self.modeButtonList:
			btn.SetUp()

	def ToggleChatMode(self, mode):
		if self.allChatMode:
			self.allChatMode = FALSE
			for i in self.CHAT_MODE_INDEX:
				chat.DisableChatMode(self.chatID, i)
			chat.EnableChatMode(self.chatID, mode)
			self.btnAll.SetUp()
		else:
			chat.ToggleChatMode(self.chatID, mode)

	def SetSize(self, width, height):
		self.imgCenter.SetRenderingRect(0.0, 0.0, float((width - self.BLOCK_WIDTH*2) - self.BLOCK_WIDTH) / self.BLOCK_WIDTH, 0.0)
		self.imgCenter.SetPosition(self.BLOCK_WIDTH, 0)
		self.imgRight.SetPosition(width - self.BLOCK_WIDTH, 0)

		self.btnClose.SetPosition(width - self.btnClose.GetWidth() - 5, 5)
		self.scrollBar.SetPosition(width - 15, 45)
		self.scrollBar.SetScrollBarSize(height - 45 - 12)
		self.scrollBar.SetPos(self.scrollBarPos)
		ui.Window.SetSize(self, width, height)

	def Open(self):
		self.OnResize()
		if not app.ENABLE_EMOTICONS_SYSTEM:
			self.chatInputSet.SetChatFocus()
		self.Show()

	def Close(self):
		if not app.ENABLE_EMOTICONS_SYSTEM:
			if self.chatInputSet:
				self.chatInputSet.KillChatFocus()
		self.Hide()

	def OnResize(self):
		x, y = self.btnSizing.GetLocalPosition()
		width = self.btnSizing.GetWidth()
		height = self.btnSizing.GetHeight()

		if x < self.CHAT_LOG_WINDOW_MINIMUM_WIDTH - width:
			self.btnSizing.SetPosition(self.CHAT_LOG_WINDOW_MINIMUM_WIDTH - width, y)
			return
		if y < self.CHAT_LOG_WINDOW_MINIMUM_HEIGHT - height:
			self.btnSizing.SetPosition(x, self.CHAT_LOG_WINDOW_MINIMUM_HEIGHT - height)
			return

		self.scrollBar.LockScroll()
		self.SetSize(x + width, y + height)
		self.scrollBar.UnlockScroll()

		if app.ENABLE_EMOTICONS_SYSTEM:
			self.lineChatLog.SetPosition(10, 16)
			self.lineChatLog.SetSize(self.GetWidth() - 35, 0)
		else:
			self.chatInputSet.SetPosition(0, 25)
			self.chatInputSet.SetSize(self.GetWidth() - 20, 20)
			self.chatInputSet.RefreshPosition()
			self.chatInputSet.SetChatMax(self.GetWidth() / 8)

	def OnScroll(self):
		self.scrollBarPos = self.scrollBar.GetPos()

		lineCount = chat.GetLineCount(self.chatID)
		visibleLineCount = chat.GetVisibleLineCount(self.chatID)
		endLine = visibleLineCount + int(float(lineCount - visibleLineCount) * self.scrollBarPos)

		chat.SetEndPos(self.chatID, self.scrollBarPos)

	def OnRunMouseWheel(self, nLen):
		if self.scrollBar.IsShow():
			if nLen > 0:
				self.scrollBar.OnUp()
			else:
				self.scrollBar.OnDown()

	def OnRender(self):
		(x, y, width, height) = self.GetRect()

		grp.SetColor(0x77000000)
		grp.RenderBar(x+width-15, y+45, 13, height-45)

		grp.SetColor(0x77000000)
		grp.RenderBar(x, y, width, height)
		grp.SetColor(0x77000000)
		grp.RenderBox(x, y, width-2, height)
		grp.SetColor(0x77000000)
		grp.RenderBox(x+1, y+1, width-2, height)

		grp.SetColor(0xff989898)
		grp.RenderLine(x+width-13, y+height-1, 11, -11)
		grp.RenderLine(x+width-9, y+height-1, 7, -7)
		grp.RenderLine(x+width-5, y+height-1, 3, -3)

		chat.ArrangeShowingChat(self.chatID)
		chat.SetPosition(self.chatID, x + 10, y + height - 25)
		chat.SetHeight(self.chatID, height - 45 - 25)
		chat.Update(self.chatID)
		chat.Render(self.chatID)

	def OnPressEscapeKey(self):
		self.Close()
		return TRUE

	def BindInterface(self, interface):
		self.interface = interface
		
	def OnMouseLeftButtonDown(self):
		hyperlink = ui.GetHyperlink()
		if hyperlink:
			if app.IsPressed(app.DIK_LALT):
				link = chat.GetLinkFromHyperlink(hyperlink)
				ime.PasteString(link)
			else:
				self.interface.MakeHyperlinkTooltip(hyperlink)

