import re
from hearthstone.enums import CardType, GameTag, Race, Rarity
from hearthstone import cardxml
from hearthstone.cardxml import CardXML


ERR_LANG_NOT_FOUND = "Language not found. Supported language keys are e.g. `enUS` or `deDE`"


db, _ = cardxml.load()


def loc_name(self, locale):
	return self.strings[GameTag.CARDNAME][locale]

def loc_text(self, locale):
	return self.strings[GameTag.CARDTEXT_INHAND][locale]

def loc_flavor(self, locale):
	return self.strings[GameTag.FLAVORTEXT][locale]

CardXML.loc_name = loc_name
CardXML.loc_text = loc_text
CardXML.loc_flavor = loc_flavor


class CardHandler():
	def __init__(self):
		self.db = {}
		for key in db.keys():
			self.db[key.lower()] = db[key]


	def handle(self, input, max_response, collectible=None):
		print("input:", input)
		term, params = self.parse_input(input)

		try:
			card = self.db[term]
			if card is not None:
				return self.stringify_card(card, params=params)
		except Exception as e:
			print(e)

		try:
			index = -1
			match = re.match(r"^(.+?)\s+(\d+)$", term)
			if match is not None:
				term = match.group(1).strip()
				index = int(match.group(2))

			term_num = None
			try:
				term_num = int(term)
			except Exception:
				pass
			cards = []
			for card in db.values():
				if collectible is None or collectible == card.collectible:
					card_name = card.name.lower()
					if (
						term_num is None and (term == ("\"%s\"" % card_name) or term in card_name)
						or term_num is not None and term_num == card.dbf_id
					):
						cards.append(card)
			num_cards = len(cards)
			print("num_cards", num_cards)
			if num_cards == 0:
				return "Card not found"
			if num_cards == 1:
				return self.stringify_card(cards[0], 0, 0, params)
			if index >= 0:
				return self.stringify_card(cards[index-1], index, num_cards, params)

			return "\n".join(
				self.stringify_card(cards[i], i + 1, num_cards, params)
				for i in range(0, min(max_response, num_cards))
			)
		except Exception as e:
			print(e)
		return "Card not found"


	def parse_input(self, input):
		parts = input.split(" --")
		term = parts[0].strip().lower()
		params = {}
		for part in parts[1:]:
			p = part.split("=")
			value = p[1] if len(p) > 1 else True
			params[p[0].lower()] = value
		return term, params


	def stringify_card(self, card, index=0, total=0, params=None):
		locale = card.locale
		tags = ""
		reqs = ""
		if params:
			if params.get("tags", False):
				tags = "\n%s" % self.get_tags(card)
			if params.get("reqs", False):
				reqs = "\n%s" % self.get_reqs(card)
			lang = params.get("lang", None)
			if lang:
				if len(lang) != 4:
					return ERR_LANG_NOT_FOUND
				locale = lang[0:2].lower() + lang[2:4].upper()
				try:
					card.loc_name(locale)
				except Exception:
					return ERR_LANG_NOT_FOUND
		health = card.durability if card.type == CardType.WEAPON else card.health
		search_index = " (%s/%s)" % (index, total) if total > 0 else ""
		stats = " %s/%s" % (card.atk, health) if card.atk + health > 0 else ""
		race = " (%s)" % (card.race.name.title()) if card.race != Race.INVALID else ""
		rarity = " %s" % card.rarity.name.title() if card.rarity != Rarity.INVALID else ""
		descr = "\n[%s Mana,%s%s %s%s]" % (card.cost, stats, rarity, card.type.name.title(), race)
		text = "\n" + card.loc_text(locale) if len(card.description) else ""
		flavor = "\n> " + card.loc_flavor(locale) if len(card.flavortext) else ""
		return (
			"```Markdown\n[%s][%s][%s]%s%s%s%s%s%s\n```"
			% (card.loc_name(locale), card.id, card.dbf_id, search_index, descr, text, flavor, tags, reqs)
		)


	def get_tags(self, card):
		return ", ".join("%s=%s" % (key.name, card.tags[key]) for key in card.tags.keys())

	def get_reqs(self, card):
		reqs = []
		for key in card.requirements.keys():
			val = "=%s" % card.requirements[key] if card.requirements[key] else ""
			reqs.append("%s%s" % (key.name, val))
		return ", ".join(reqs)
