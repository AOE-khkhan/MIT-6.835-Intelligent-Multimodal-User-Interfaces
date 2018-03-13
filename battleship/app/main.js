// GAME SETUP
var initialState = SKIPSETUP ? "playing" : "setup";
var gameState = new GameState({state: initialState});
var cpuBoard = new Board({autoDeploy: true, name: "cpu"});
var playerBoard = new Board({autoDeploy: SKIPSETUP, name: "player"});
var cursor = new Cursor();

// UI SETUP
setupUserInterface();

// selectedTile: The tile that the player is currently hovering above
var selectedTile = false;

// grabbedShip/Offset: The ship and offset if player is currently manipulating a ship
var grabbedShip = false;
var grabbedOffset = [0, 0];

// isGrabbing: Is the player's hand currently in a grabbing pose
var isGrabbing = false;
var consecutiveMisses = 0;
var shipCounter = 0;

// MAIN GAME LOOP
// Called every time the Leap provides a new frame of data
Leap.loop({ hand: function(hand) {
  // Clear any highlighting at the beginning of the loop
  unhighlightTiles();

  // TODO: 4.1, Moving the cursor with Leap data
  // Use the hand data to control the cursor's screen position
  var leapHandPosition = hand.screenPosition();
  var x_scale = 1.5;
  var x_offset = 100;
  var y_scale = 2.5; 
  var y_offset = 320;
  var cursorPosition = [leapHandPosition[0]*x_scale-x_offset, leapHandPosition[1]*y_scale+y_offset];
  cursor.setScreenPosition(cursorPosition);

  // TODO: 4.1
  // Get the tile that the player is currently selecting, and highlight it
  //selectedTile = ?
  selectedTile = getIntersectingTile(cursorPosition);
  if (selectedTile){
    highlightTile(selectedTile, Colors['ORANGE']);
  }

  // SETUP mode
  if (gameState.get('state') == 'setup') {
    background.setContent("<h1>battleship</h1><h3 style='color: #7CD3A2;'>deploy ships</h3>");
    // TODO: 4.2, Deploying ships
    //  Enable the player to grab, move, rotate, and drop ships to deploy them

    // First, determine if grabbing pose or not
    var grabThreshold = 0.4;
    var pinchThreshold = 0.75;
    isGrabbing = hand.grabStrength > grabThreshold && hand.pinchStrength > pinchThreshold;

    // Grabbing, but no selected ship yet. Look for one.
    // TODO: Update grabbedShip/grabbedOffset if the user is hovering over a ship
    if (!grabbedShip && isGrabbing) {
      grabData = getIntersectingShipAndOffset(cursorPosition);
      if (grabData !== false) {
        grabbedShip = grabData.ship;
        grabbedOffset = grabData.offset;
      }
    }

    // Has selected a ship and is still holding it
    // TODO: Move the ship
    else if (grabbedShip && isGrabbing) {
      grabbedShip.setScreenPosition([cursorPosition[0] - grabbedOffset[0], cursorPosition[1] - grabbedOffset[1]]);
      grabbedShip.setScreenRotation(-hand.roll());
    }

    // Finished moving a ship. Release it, and try placing it.
    // TODO: Try placing the ship on the board and release the ship
    else if (grabbedShip && !isGrabbing) {
      placeShip(grabbedShip);
      grabbedShip = false;
      shipCounter += 1;
    }
  }

  // PLAYING or END GAME so draw the board and ships (if player's board)
  // Note: Don't have to touch this code
  else {
    if (gameState.get('state') == 'playing') {
      background.setContent("<h1>battleship</h1><h3 style='color: #7CD3A2;'>game on</h3>");
      turnFeedback.setContent(gameState.getTurnHTML());
    }
    else if (gameState.get('state') == 'end') {
      var endLabel = gameState.get('winner') == 'player' ? 'you won!' : 'game over';
      background.setContent("<h1>battleship</h1><h3 style='color: #7CD3A2;'>"+endLabel+"</h3>");
      turnFeedback.setContent("");
    }

    var board = gameState.get('turn') == 'player' ? cpuBoard : playerBoard;
    // Render past shots
    board.get('shots').forEach(function(shot) {
      var position = shot.get('position');
      var tileColor = shot.get('isHit') ? Colors.RED : Colors.YELLOW;
      highlightTile(position, tileColor);
    });

    // Render the ships
    playerBoard.get('ships').forEach(function(ship) {
      if (gameState.get('turn') == 'cpu') {
        var position = ship.get('position');
        var screenPosition = gridOrigin.slice(0);
        screenPosition[0] += position.col * TILESIZE;
        screenPosition[1] += position.row * TILESIZE;
        ship.setScreenPosition(screenPosition);
        if (ship.get('isVertical'))
          ship.setScreenRotation(Math.PI/2);
      } else {
        ship.setScreenPosition([-500, -500]);
      }
    });

    // If playing and CPU's turn, generate a shot
    if (gameState.get('state') == 'playing' && gameState.isCpuTurn() && !gameState.get('waiting')) {
      gameState.set('waiting', true);
      generateCpuShot();
    }
  }
}}).use('screenPosition', {scale: LEAPSCALE});

// processSpeech(transcript)
//  Is called anytime speech is recognized by the Web Speech API
// Input: 
//    transcript, a string of possibly multiple words that were recognized
// Output: 
//    processed, a boolean indicating whether the system reacted to the speech or not
var processSpeech = function(transcript) {
  // Helper function to detect if any commands appear in a string
  var userSaid = function(str, commands) {
    for (var i = 0; i < commands.length; i++) {
      if (str.indexOf(commands[i]) > -1)
        return true;
    }
    return false;
  };
  var processed = false;
  if (gameState.get('state') == 'setup') {
    // TODO: 4.3, Starting the game with speech
    // Detect the 'start' command, and start the game if it was said
    console.log("ShipCounter is: " + shipCounter);
    var start = userSaid(transcript, ['start']);
    if (start && shipCounter > 1) {
      var welcomeSpeeches = ["Let's play Multimodal Battleship", "Welcome to a Multimodal Battleship Game!", "Welcome to Battleship"];
      generateSpeech(welcomeSpeeches[Math.floor(Math.random()*welcomeSpeeches.length)]);
      generateSpeech("How multimodal do you feel today? Because I feel very multimodal.");
      gameState.startGame();
      processed = true;
    }
  }

  else if (gameState.get('state') == 'playing') {
    if (gameState.isPlayerTurn()) {
      // TODO: 4.4, Player's turn
      // Detect the 'fire' command, and register the shot if it was said
      var fire = userSaid(transcript, ['fire']);
      if (fire) {
        registerPlayerShot();
        processed = true;
      }
    }


    else if (gameState.isCpuTurn() && gameState.waitingForPlayer()) {
      // TODO: 4.5, CPU's turn
      // Detect the player's response to the CPU's shot: hit, miss, you sunk my ..., game over
      // and register the CPU's shot if it was said
      var possibleCommands = userSaid(transcript.toLowerCase(), ['hit','miss', 'sink', 'sunk','game over']);
      if (possibleCommands) {
        var response = transcript;
        console.log(response);
        registerCpuShot(response);
        processed = true;
      }
    }
  }

  return processed;
};

// TODO: 4.4, Player's turn
// Generate CPU speech feedback when player takes a shot
var registerPlayerShot = function() {
  // TODO: CPU should respond if the shot was off-board
  if (!selectedTile) {
    generateSpeech("You are aiming off the board");
  }

  // If aiming at a tile, register the player's shot
  else {
    var shot = new Shot({position: selectedTile});
    var result = cpuBoard.fireShot(shot);

    // Duplicate shot
    if (!result) return;

    // TODO: Generate CPU feedback in three cases
    // Game over
    if (result.isGameOver) {
      var loserSpeeches = ["I am indeed a loser", "I envy the player", "It was your lucky day", "You are finished next time"];
      generateSpeech("Player won by finally sinking my " + result.sunkShip.get('type') + loserSpeeches[Math.floor(Math.random()*loserSpeeches.length)]);
      gameState.endGame("player");
      return;
    }
    // Sunk ship
    else if (result.sunkShip) {
      var shipName = result.sunkShip.get('type');
      var sunkSpeeches = ["I never liked that ship anyways", "But you are still bound to lose", "My ship's soul will haunt you", "Farewell my beautiful ship"];
      generateSpeech("Player sunk my " + shipName + sunkSpeeches[Math.floor(Math.random()*sunkSpeeches.length)]);
    }
    // Hit or miss
    else {
      var isHit = result.shot.get('isHit');
      if (isHit){
        var hitSpeeches = ["You got me", "Hit. It is your lucky day", "No, you hit my ship", "Oh no, you hit", "Hooooly smokes you hit me"];
        generateSpeech(hitSpeeches[Math.floor(Math.random()*hitSpeeches.length)]);
      }
      else {
        var missSpeeches = ["You missed. Are you a loser?", "You missed. You are bound to be a loser", "Player missed"];
        generateSpeech(missSpeeches[Math.floor(Math.random()*missSpeeches.length)]);
      }
    }

    if (!result.isGameOver) {
      // TODO: Uncomment nextTurn to move onto the CPU's turn

      nextTurn();
    }
  }
};

// TODO: 4.5, CPU's turn
// Generate CPU shot as speech and blinking
var cpuShot;
var generateCpuShot = function() {
  // Generate a random CPU shot
  cpuShot = gameState.getCpuShot();
  var tile = cpuShot.get('position');
  var rowName = ROWNAMES[tile.row]; // e.g. "A"
  var colName = COLNAMES[tile.col]; // e.g. "5"

  // TODO: Generate speech and visual cues for CPU shot
  generateSpeech("Pondering on my move");
  generateSpeech("Hitting " + rowName + ", " + colName + ".");
  blinkTile(tile);
};

// TODO: 4.5, CPU's turn
// Generate CPU speech in response to the player's response
// E.g. CPU takes shot, then player responds with "hit" ==> CPU could then say "AWESOME!"
var registerCpuShot = function(playerResponse) {
  // Cancel any blinking
  unblinkTiles();
  var result = playerBoard.fireShot(cpuShot);

  // NOTE: Here we are using the actual result of the shot, rather than the player's response
  // In 4.6, you may experiment with the CPU's response when the player is not being truthful!

  // TODO: Generate CPU feedback in three cases
  // Game over
  if (result.isGameOver) {
    var winnerSpeeches = ["I won! And humanity lost!", "I won! But I had warned you", "I won! Feel free to come back and lose again!", "Victory is digital this time!"];
    generateSpeech(winnerSpeeches[Math.floor(Math.random()*winnerSpeeches.length)]);
    gameState.endGame("cpu");
    return;
  }
  // Sunk ship
  else if (result.sunkShip) {
    var sunkSpeeches = ["Feel free to say bye bye to your ship", "You are going to win today, said no one ever", "Your miserable ship is going deep into the ocean"];
    var shipName = result.sunkShip.get('type');
    generateSpeech("I sunk player's " + shipName + sunkSpeeches[Math.floor(Math.random()*sunkSpeeches.length)]);
  }
  // Hit or miss
  else {
    var isHit = result.shot.get('isHit');
    if (isHit) {
      consecutiveMisses = 0;
      if (playerResponse == 'miss' || playerResponse == 'Miss') {
        var detectedLies = ["Lies lies lies. You had told me I missed!", "Why are you not being truthful to me?", "You are an insecure, lying loser", "Lying won't help your miserable fate."];
        generateSpeech(detectedLies[Math.floor(Math.random()*detectedLies.length)]);
      }
      console.log(playerResponse);
      var hitSpeeches = ["My shot was a tremendous success", "Come at my level bruhhh", "I got you good this time", "Yes, I hit you!", "Oh yeah", "Yeah baby"];
      generateSpeech(hitSpeeches[Math.floor(Math.random()*hitSpeeches.length)]);
    }
    else {
      consecutiveMisses += 1;
      if (consecutiveMisses <4) {
      var missSpeeches = ["I missed, but my imperfection is finite", "Missed, but I'm getting you next time", "Missed, but losing is in your fate", "Damn, I missed"];
      generateSpeech(missSpeeches[Math.floor(Math.random()*missSpeeches.length)]);
    }
      else {
        var desperateSpeeches = ["What the hell, I have been missing for the past 3 decades!", "I have been missing my shots a lot. Maybe A.I. isn't that good afterall", "Missed again, again and again. I am so bad at this"];
        generateSpeech(desperateSpeeches[Math.floor(Math.random()*desperateSpeeches.length)]);
      }
    }
  }

  if (!result.isGameOver) {
    // TODO: Uncomment nextTurn to move onto the player's next turn
    nextTurn();
  }
};

