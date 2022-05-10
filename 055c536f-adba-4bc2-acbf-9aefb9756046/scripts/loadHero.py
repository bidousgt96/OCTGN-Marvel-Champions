#------------------------------------------------------------
# 'Load Hero' event
#------------------------------------------------------------

def loadHero(group, x = 0, y = 0):
    mute()
    if not deckNotLoaded(group, checkGroup = [c for c in me.Deck if not isEncounter([c])]):
        confirm("Cannot generate a deck: You already have cards loaded.  Reset the game in order to generate a new deck.")
        return

    choice = askChoice("What type of deck do you want to load?", ["An out of the box deck", "A downloaded deck (.o8d file)", "A marvelcdb deck (URL)"])

    if choice == 0: return
    if choice == 1:
        for i in sorted(hero_setup.keys()):
            me.piles["Removed"].create(i, 1)
        dlg = cardDlg(me.piles["Removed"])
        dlg.title = "Select your Hero"
        dlg.text = "Select your Hero :"
        cardsSelected = dlg.show()
        if cardsSelected is None:
            deleteCards(me.piles["Removed"])
            return
        else:
            for card in cardsSelected:
                deckname = createCards(me.Deck,sorted(eval(card.Owner).keys()), eval(card.Owner))
            changeOwner(deckname, card.Owner)
            deleteCards(me.piles["Removed"])

    if choice == 2:
        filename = openFileDlg('', '', 'o8d Files|*.o8d')
        if filename is None:
            return        
        deckname = o8dLoad(filename)

    if choice == 3:
        url = askString("Please enter the URL of the deck you wish to load.", "")
        if url == None: return
        if not "view/" in url:
            whisper("Error: Invalid URL.")
            return
        deckname = createAPICards(url)

    tableSetup()

def unloadHeroDeck(group, x=0, y=0):
    """
    Remove all cards for one player: in hand, in piles and on table.
    Highly inspired from SDA OCTGN implementation
    """
    mute()
    for p in me.piles:
        notify("{} removes cards from {}.".format(me, p))
        [c.delete() for c in me.piles[p] if c.owner == me]

    notify("Removing cards from {}'s hand.".format(me))
    [c.delete() for c in me.hand if c.owner == me]

    hero_cards = [c.Owner for c in group if c.owner == me and c.Type in ["hero", "alter_ego"]]
    if len(hero_cards) == 1:
        hero_id = hero_cards[0]
        notify("Removing {}'s cards from table.".format(me))
        [c.delete() for c in group if c.owner == me and c.Owner in [hero_id, "{}_nemesis".format(hero_id)]]

def heroSetup(group=table, x = 0, y = 0):

    id = myID() # This ensures we have a unique ID based on our position in the setup order
    heroCount = countHeros(me)

    # Find any Permanent cards
    #permanents = filter(lambda card: "Permanent" in card.Keywords or "Permanent." in card.Text, me.deck)

    # Move Hero to the table
    newHero = False
    hero = filter(lambda card: card.Type == "hero", me.Deck)
    if hero:
        heroCount += 1
        newHero = True
        heroCard = hero[0]
        heroCard.moveToTable(playerX(id),tableLocations['hero'][1])
        heroCard.alternate = 'b'
        # heroCard.markers[HealthMarker] += num(heroCard.HP)
        setHeroCounters(heroCard)
        notify("{} places his Hero on the table".format(me))

    if newHero:
        me.deck.shuffle()
        createCards(heroCard.owner.piles["Nemesis"],nemesis[str(heroCard.properties["Owner"])].keys(),nemesis[str(heroCard.properties["Owner"])])       

        #------------------------------------------------------------
        # Specific Hero setup
        #------------------------------------------------------------

        # Doctor Strange
        if str(heroCard.properties["Owner"]) == 'doctor_strange':
            createCards(me.piles['Special Deck'],special_decks['doctor_strange'].keys(),special_decks['doctor_strange'])
            me.piles['Special Deck'].collapsed = False
            me.piles['Special Deck Discard'].collapsed = False

        # Spectrum
        if str(heroCard.properties["Owner"]) == 'spectrum':
            for c in filter(lambda card: card.Type == "upgrade", me.Deck):
                if c.CardNumber == "21002" or c.CardNumber == "21003" or c.CardNumber == "21004":
                    c.moveTo(me.piles['Special Deck'])
            me.piles['Special Deck'].collapsed = False
            me.piles['Special Deck'].visibility = "all"

        # Valkyrie
        if str(heroCard.properties["Owner"]) == 'valk':
            for c in filter(lambda card: card.Type == "upgrade", me.Deck):
                if c.CardNumber == "25002":
                    c.moveTo(me.piles['Special Deck'])
            me.piles['Special Deck'].collapsed = False
            me.piles['Special Deck'].visibility = "all"

        # Vision
        if str(heroCard.properties["Owner"]) == 'vision':
            for c in filter(lambda card: card.Type == "upgrade", me.Deck):
                if c.CardNumber == "26002a":
                    c.moveToTable(playerX(id)+70,tableLocations['hero'][1])

        # Ironheart
        if str(heroCard.properties["Owner"]) == 'ironheart':
            for c in filter(lambda card: card.Type == "hero", me.Deck):
                c.moveTo(me.piles['Special Deck'])
            me.piles['Special Deck'].collapsed = False
            me.piles['Special Deck'].visibility = "all"

        #------------------------------------------------------------
        # Draw Opening Hand
        #------------------------------------------------------------

        if len(me.hand) == 0:
            drawOpeningHand()

#------------------------------------------------------------
# 'Load Hero' specific functions
#------------------------------------------------------------

def o8dLoad(o8d):
    with open(o8d, "rt") as f:
        lines = f.readlines()

    start_deck = False
    end_deck = False
    hero_id = ""
    all_cards = []
    for line in lines:
        if line.find('<section name="Cards"') > -1:
            start_deck = True
        if start_deck and line.find('</section>') > -1:
            end_deck = True
        if start_deck and not end_deck:
            matches = re.search('<card qty=\"(\d+)\" id=\"([a-zA-Z0-9-]+)\"', line, re.IGNORECASE)
            if matches:
                if matches.group(1) is not None and matches.group(2) is not None:
                    qty = int(matches.group(1))
                    card_id = matches.group(2)
                    cards = me.Deck.create(card_id, qty)
                    if qty == 1:
                        all_cards.append(cards)
                        if cards.Type == "hero":
                            hero_id = cards.Owner
                    else:
                        all_cards.extend(cards)
                else:
                    whisper("Error loading deck: Unknown card found.  Please restart game and try a different deck.")
    changeOwner(all_cards, hero_id)

def changeOwner(cards, hero_id):
    """
    Change Owner property of a given list of cards if Owner is unknown (or aspect card).
    """
    for card in cards:
        if card.Owner is None or card.Owner in ["", "basic", "justice", "leadership", "protection", "aggression"]:
            card.Owner = hero_id

def createAPICards(url):
    all_cards = []
    if "decklist/" in str(url):
        deckid = url.split("view/")[1].split("/")[0]
        data, code = webRead("https://marvelcdb.com/api/public/decklist/{}".format(deckid))
    elif "deck/" in str(url):
        deckid = url.split("view/")[1].split("/")[0]
        data, code = webRead("https://marvelcdb.com/api/public/deck/{}".format(deckid))
    if code != 200:
        whisper("Error retrieving online deck data, please try again.")
        return
    try:
        deckname = JavaScriptSerializer().DeserializeObject(data)["name"]
        deck = JavaScriptSerializer().DeserializeObject(data)["slots"]
        hero = JavaScriptSerializer().DeserializeObject(data)["investigator_code"]
        chars_to_remove = ['[',']']
        rx = '[' + re.escape(''.join(chars_to_remove)) + ']'
        for id in deck:
            line = re.sub(rx,'',str(id))
            line = line.split(',')
            cardid = line[0]
            qty = int(line[1].strip())
            card = me.Deck.create(card_mapping[cardid], qty)
            if card == None:
                whisper("Error loading deck: Unknown card found.  Please restart game and try a different deck.")
            if qty == 1:
                all_cards.append(card)
            else:
                all_cards.extend(card)
        hero_card = me.Deck.create(card_mapping[hero])
        changeOwner(all_cards, hero_card.Owner)
        return deckname
    except ValueError:
        whisper("Error retrieving online deck data, please try again. If you are trying to load a non published deck make sure you have edited your account to select 'Share Your Decks'")