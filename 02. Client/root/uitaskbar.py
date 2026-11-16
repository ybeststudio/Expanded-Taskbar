# Ara:
			if self.Gem:
				self.Gem.SetText(localeInfo.NumberToString(player.GetGem()))

# Altina ekle:
class ExpandedTaskBar(ui.ScriptWindow):
	BUTTON_DRAGON_SOUL = 0
	BUTTON_SWITCHBOT = 4
	BUTTON_WIKI = 5
	BUTTON_PET_INFO = 8
	BUTTON_HUNTING = 20
	BUTTON_AUTO_WINDOW = 21

	BUTTON_STEP = 36
	BUTTON_SIZE = 37
	CENTER_OFFSET_X = 51
	CHAT_GAP = 16
	ICON_HEIGHT = 32

	BUTTON_NAMES = (
		(BUTTON_DRAGON_SOUL, "DragonSoulButton"),
		(BUTTON_SWITCHBOT, "SwitchbotButton"),
		(BUTTON_WIKI, "WikiButton"),
		(BUTTON_PET_INFO, "PetInfoButton"),
		(BUTTON_HUNTING, "HuntingButton"),
		(BUTTON_AUTO_WINDOW, "AutoButton"),
	)

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.SetWindowName("ExpandedTaskBar")

		self.exclusion_list = []
		self.toggleButtonDict = {}
		self.buttonOrder = []
		self.interface = None
		self.chatTop = None
		self.chatCenterX = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/ExpandedTaskBar.py")
		except:
			import exception
			exception.Abort("ExpandedTaskBar.LoadWindow.LoadObject")

		self.expandedTaskBarBoard = self.GetChild("ExpanedTaskBar_Board")

		self.toggleButtonDict = {}
		self.buttonOrder = []
		for key, name in ExpandedTaskBar.BUTTON_NAMES:
			if not self.IsChild(name):
				continue

			button = self.GetChild(name)
			button.SetParent(self)
			self.toggleButtonDict[key] = button
			self.buttonOrder.append(key)

		if ExpandedTaskBar.BUTTON_SWITCHBOT in self.toggleButtonDict:
			self.toggleButtonDict[ExpandedTaskBar.BUTTON_SWITCHBOT].SetEvent(ui.__mem_func__(self.OnClickSwitchbot))

		self.RePositionButton()

	def RePositionButton(self):
		visible = [key for key in self.buttonOrder if key not in self.exclusion_list]
		for key in self.buttonOrder:
			if key in self.exclusion_list:
				self.toggleButtonDict[key].Hide()

		total_width = ExpandedTaskBar.BUTTON_STEP * max(0, len(visible) - 1) + ExpandedTaskBar.BUTTON_SIZE
		window_x = wndMgr.GetScreenWidth() / 2 + ExpandedTaskBar.CENTER_OFFSET_X - total_width / 2
		window_y = wndMgr.GetScreenHeight() - 74
		if self.chatTop is not None:
			window_y = min(window_y, self.chatTop - ExpandedTaskBar.CHAT_GAP - ExpandedTaskBar.ICON_HEIGHT)
			if self.chatCenterX is not None:
				window_x = self.chatCenterX - total_width / 2

		self.SetSize(total_width, ExpandedTaskBar.BUTTON_SIZE)
		self.expandedTaskBarBoard.SetSize(total_width, ExpandedTaskBar.BUTTON_SIZE)
		self.SetPosition(window_x, window_y)

		pos_x = 0
		for key in visible:
			self.toggleButtonDict[key].SetPosition(pos_x, 0)
			self.toggleButtonDict[key].Show()
			pos_x += ExpandedTaskBar.BUTTON_STEP

	def SetChatTop(self, chatTop, centerX = None):
		if chatTop is not None:
			chatTop = int(chatTop)
		if centerX is not None:
			centerX = int(centerX)
		if chatTop == self.chatTop and centerX == self.chatCenterX:
			return
		self.chatTop = chatTop
		self.chatCenterX = centerX
		self.RePositionButton()

	def SetTop(self):
		super(ExpandedTaskBar, self).SetTop()
		for button in self.toggleButtonDict.values():
			button.SetTop()

	def Show(self):
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.Hide()

	def SetToolTipText(self, eButton, text):
		if eButton in self.toggleButtonDict:
			self.toggleButtonDict[eButton].SetToolTipText(text)

	def SetToggleButtonEvent(self, eButton, kEventFunc):
		if eButton in self.toggleButtonDict:
			self.toggleButtonDict[eButton].SetEvent(kEventFunc)

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def BindInterfaceClass(self, interface):
		self.interface = interface

	def OnClickSwitchbot(self):
		if app.ENABLE_RENEWAL_SWITCHBOT and self.interface:
			self.interface.ToggleSwitchbotWindow()

