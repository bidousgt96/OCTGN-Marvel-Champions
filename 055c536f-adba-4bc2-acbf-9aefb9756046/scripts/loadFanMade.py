#------------------------------------------------------------
# 'Load FanMade' events
#------------------------------------------------------------

def loadFanMade_Hero(group, x = 0, y = 0):
    mute()
    if not deckNotLoaded(group, checkGroup = [c for c in me.Deck if not isEncounter([c])]):
        confirm("Cannot generate a deck: You already have cards loaded.  Reset the game in order to generate a new deck.")
        return

    o8d = openFileDlg('Select fan made o8d deck to load', '', 'o8d Files|*.o8d')
    if o8d is None:
         return        
    full_dict = o8dLoadAsDict(o8d)

    hero_id = ""
    all_cards = []
    aspect_cards = []

    # 1- Load Hero cards + Nemesis + Special Deck cards
    # Cards without Owner are considered to be Aspect ones
    for section_id, section_elements in full_dict.items():
        if not section_elements["shared"]:
            # Manage in which pile cards will be created: Deck, Special Deck or Nemesis
            destination_pile = me.Deck
            if section_elements["section"] == "Nemesis":
                destination_pile = me.piles["Nemesis"]
            if section_elements["section"] == "Special":
                destination_pile = me.piles["Special Deck"]
            
            # Create cards
            for card_id,qty in section_elements["cards"].items():
                cards = destination_pile.create(card_id, qty)
                if qty == 1:
                    all_cards.append(cards)
                    if cards.Type == "hero":
                        hero_id = cards.Owner
                    if cards.Owner == "":
                        aspect_cards.append(cards)
                else:
                    all_cards.extend(cards)
                    if cards[0].Owner == "":
                        aspect_cards.extend(cards)
    changeOwner(all_cards, hero_id)

    # 2- If some aspect cards have been found, let player choose to load them or not
    do_step3 = False
    if len(aspect_cards) > 0:
        choice = askChoice("Do you want to also load the prebuilt hero cards from this .o8d file?", ["Yes", "No"])
        # No answer or 'Yes' have the same effect: we load those cards
        if choice == 2:
            do_step3 = True
            # Remove them from deck as they have already been created
            [c.delete() for c in me.Deck if c in aspect_cards]

    # 3- Load aspect cards from somewhere else if player has chosen to do so or if there were no such cards in the loaded o8d file
    if do_step3:
        choice_step3 = askChoice("Select where to load other aspect cards from:", ["Another .o8d file", "Another marvelcdb deck (URL)", "A Universal Pre-Built deck"])
        if choice_step3 == 0: return
        if choice_step3 == 1:
            other_o8d = openFileDlg('', '', 'o8d Files|*.o8d')
            if other_o8d is None:
                return        
            other_deck = o8dLoadAsDict(other_o8d)

            other_cards = []
            for card_id,qty in other_deck["Cards_False"]["cards"].items():
                cards = me.piles["Setup"].create(card_id, qty)
                if qty == 1 and cards.Owner == "":
                    other_cards.append(cards)
                elif qty > 1 and cards[0].Owner == "":
                    other_cards.extend(cards)
            changeOwner(other_cards, hero_id)
            [c.moveTo(me.Deck) for c in other_cards]
            deleteCards(me.piles["Setup"]) 
        
        if choice_step3 == 2:
            url = askString("Please enter the URL of the deck you wish to load.", "")
            if url == None: return
            if not "view/" in url:
                whisper("Error: Invalid URL.")
                return
            createAPICards(url, True, new_owner=hero_id)
        
        if choice_step3 == 3:
            upb = sorted(universal_prebuilt.keys())
            pb_choice = askChoice("What Universal Pre-Built deck do you want to load?", upb)
            createAPICards("https://marvelcdb.com/deck/view/{}".format(universal_prebuilt[upb[pb_choice-1]]), True, new_owner=hero_id)

    tableSetup()

def loadFanMade_Villain(group, x = 0, y = 0):
    mute()
    villainName = ''
    nbModular = 1

    if not deckNotLoaded(group,0,0,shared.villain):
        confirm("Cannot generate a deck: You already have cards loaded. Reset the game in order to generate a new deck.")
        return

    # Fonction permettant de télécharger le deck :
        # - Inclure toutes les sections "shared=True"
        # - Pour la section "Recommended_Modular", demander si on veut charger le recommandé ou non. Si on ne veut pas alors demander quel set(s) 
		# on veut charger. (Inclure la possibilité d'aller chercher un set FanMade qui devra être chargé directement dans le deck rencontre)

    villainName = (c[0].Name for c in shared.villain)
    setGlobalVariable("villainSetup",str(villainName))

    update()

    cardsSelected = [c for c in setupPile()]
    for card in cardsSelected:
        createCards(shared.encounter, eval(card.Owner).keys(), eval(card.Owner))
    deleteCards(setupPile())
    loadDifficulty()
    notify('{} loaded {}, Good Luck!'.format(me, villainName))
    tableSetup(doPlayer=False,doEncounter=False)

def loadFanMade_Modular(group, x = 0, y = 0):
    mute()

    # Fonction permettant de télécharger le deck :
        # - Inclure toutes les sections "shared=True"