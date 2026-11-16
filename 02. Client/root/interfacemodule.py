# Interface.__init__ icinde ara:
		self.DRAGON_SOUL_IS_QUALIFIED = FALSE
		self.wndExpandedMoney = None

# Altina ekle:
		self.wndExpandedTaskBar = None


# Interface.__MakeTaskBar icinde ara:
		self.wndExpandedMoneyTaskBar = uiTaskBar.ExpandedMoneyTaskBar()
		if uiTaskBar.TaskBar.IS_EXPANDED:

# Altina ekle:
			self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_EXPAND, ui.__mem_func__(self.ToggleExpandedButton))
			self.wndExpandedTaskBar = uiTaskBar.ExpandedTaskBar()
			self.wndExpandedTaskBar.LoadWindow()


# Interface.__MakeTaskBar icinde ara:
			# Interface class'?n? ba?la

# Altina ekle:
			self.wndExpandedTaskBar.BindInterfaceClass(self)


# Interface.__MakeTaskBar icinde ara:
			if app.ENABLE_GROWTH_PET_SYSTEM:

# Altina ekle:
				self.PetInformationActivate()
				self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_PET_INFO, ui.__mem_func__(self.TogglePetInformationWindow))


# Interface.__MakeTaskBar icinde ara:
			if app.ENABLE_WIKI_SYSTEM:

# Altina ekle:
				self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_WIKI, ui.__mem_func__(self.OpenWikiWindow))


# Interface.__MakeTaskBar icinde ara:
			if app.ENABLE_HUNTING_SYSTEM:

# Altina ekle:
				self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_HUNTING, ui.__mem_func__(self.ToggleHuntingWindow))


# Interface.__MakeTaskBar icinde ara:
			if app.__AUTO_HUNT__:

# Altina ekle:
				self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_AUTO_WINDOW, ui.__mem_func__(self.ToggleAutoHuntWindow))


# Interface.Close icinde ara:
			self.wndEnergyCrystal.Destroy()
			self.wndEnergyCrystal = None

# Altina ekle:
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.Destroy()


# Interface.Close icinde ara:
		del self.wndChat
		del self.wndTaskBar

# Altina ekle:
		if self.wndExpandedTaskBar:
			del self.wndExpandedTaskBar


# Interface.ShowAllWindows icinde ara:
		self.wndChat.Show()
		self.wndMiniMap.Show()

# Altina ekle:
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.Show()
			self.wndExpandedTaskBar.SetTop()


# Interface.HideAllWindows icinde ara:
		if self.wndGuild:
			self.wndGuild.Hide()

# Altina ekle:
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.Hide()


# Interface icinde ara:
			if self.wndAutoChat:
				self.wndAutoChat.Toggle()

# Altina ekle:
	def ToggleExpandedButton(self):
		if False == player.IsObserverMode():
			if False == self.wndExpandedTaskBar.IsShow():
				self.wndExpandedTaskBar.Show()
				self.wndExpandedTaskBar.SetTop()
			else:
				self.wndExpandedTaskBar.Close()


# Interface icinde ara:
			self.wndExpandedMoneyTaskBar.Close()
	if app.ENABLE_GROWTH_PET_SYSTEM:

# Altina ekle:
		def PetInformationActivate(self):
			if uiTaskBar.TaskBar.IS_EXPANDED:
				self.wndExpandedTaskBar.SetToolTipText(uiTaskBar.ExpandedTaskBar.BUTTON_PET_INFO, uiScriptLocale.TASKBAR_PET_INFO)


# Interface icinde ara:
			self.wndCubeResult.SetTop()
	if constInfo.ENABLE_EXPANDED_TASKBAR:

# Altina ekle:
		def PressExpandedTaskbar(self):
			if self.wndExpandedTaskBar.IsShow():
				self.wndExpandedTaskBar.Hide()
			else:
				self.wndExpandedTaskBar.Show()


# Interface.__HideWindows icinde ara:
						self.wndParty,\
						self.wndGameButton,

# Altina ekle:
		if self.wndExpandedTaskBar:
			hideWindows += self.wndExpandedTaskBar,

