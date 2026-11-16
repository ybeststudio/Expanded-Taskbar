# ChatWindow.__RefreshTaskBarPosition icinde ara:
	def __RefreshTaskBarPosition(self):

# Altina ekle:
		if not self.interface or not self.interface.wndExpandedTaskBar:
			return


# ChatWindow.__RefreshTaskBarPosition icinde ara:
			(btnX, btnY) = self.btnChatSizing.GetGlobalPosition()
			(x, y, width, height) = self.GetRect()

# Altina ekle:
			self.interface.wndExpandedTaskBar.SetChatTop(btnY, x + width / 2)


# ChatWindow.__RefreshTaskBarPosition icinde ara:
		else:

# Altina ekle:
			self.interface.wndExpandedTaskBar.SetChatTop(None)

