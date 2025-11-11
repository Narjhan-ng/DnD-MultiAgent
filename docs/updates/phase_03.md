# Phase 03 - Dynamic Character Creator

**Data Inizio**: TBD (dopo Phase 02)
**Durata Stimata**: 2-3 giorni
**Status**: 🔵 Pianificata

---

## Recap Fase Precedente

**Phase 02 - Dual Input Mode (Voice + Text)** (Da Completare)

Nella Phase 02 abbiamo aggiunto input vocale flessibile per giocatori umani:
- ✅ Web Speech API integration (browser-based STT)
- ✅ Hold-to-speak button con visual feedback
- ✅ Dual input mode: voice O text, scelta libera
- ✅ Settings panel (language, auto-submit, voice mode)
- ✅ Browser compatibility detection + fallback
- ✅ Mobile-responsive voice controls

**Limitazione attuale**: I giocatori possono scegliere solo tra i **personaggi predefiniti** (Thorin, Elara, Finn). Non è possibile creare personaggi personalizzati.

---

## Obiettivi Phase 03

Questa fase introduce un **Character Creator dinamico** che permette agli utenti di creare personaggi D&D 5e personalizzati con assistenza AI:

- **Form UI**: L'utente inserisce dati base (nome, classe, razza, personalità, background)
- **AI Generation**: LLM genera automaticamente stats, skills, equipment, spells (se caster)
- **Validation**: Sistema valida che il personaggio rispetti le regole D&D 5e
- **Gallery**: Tutti i personaggi (default + custom) disponibili nella lobby
- **Persistence**: Personaggi salvati in YAML per riutilizzo futuro

### Approccio: Generazione Assistita AI
L'utente fornisce input creativi (personalità, backstory), l'AI genera i dettagli tecnici (ability scores ottimizzati, equipment appropriato) rispettando rigorosamente le regole D&D 5e.

---

## Componenti da Implementare

### 3.1 Character Creator UI

**File**: `src/ui/frontend/character_creator.html` (NUOVO)

#### Layout Completo

```html
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Character Creator - D&D Multi-Agent System</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="creator-container">
        <header>
            <h1>🎲 Create Your Character</h1>
            <p>Fill in the details below and let AI generate your D&D 5e character sheet</p>
        </header>

        <form id="character-form">
            <!-- Basic Info -->
            <section class="form-section">
                <h2>Basic Information</h2>

                <div class="form-group">
                    <label for="char-name">Character Name *</label>
                    <input
                        type="text"
                        id="char-name"
                        required
                        placeholder="e.g., Thorin Ironforge"
                    />
                </div>

                <div class="form-group">
                    <label for="char-class">Class *</label>
                    <select id="char-class" required>
                        <option value="">-- Select Class --</option>
                        <option value="Fighter">Fighter</option>
                        <option value="Wizard">Wizard</option>
                        <option value="Rogue">Rogue</option>
                        <option value="Cleric">Cleric</option>
                        <option value="Ranger">Ranger</option>
                        <option value="Paladin">Paladin</option>
                        <option value="Barbarian">Barbarian</option>
                        <option value="Bard">Bard</option>
                        <option value="Druid">Druid</option>
                        <option value="Warlock">Warlock</option>
                    </select>
                    <small class="help-text">The character's class determines their abilities and role in the party</small>
                </div>

                <div class="form-group">
                    <label for="char-race">Race *</label>
                    <select id="char-race" required>
                        <option value="">-- Select Race --</option>
                        <option value="Human">Human</option>
                        <option value="Elf">Elf</option>
                        <option value="Dwarf">Dwarf</option>
                        <option value="Halfling">Halfling</option>
                        <option value="Dragonborn">Dragonborn</option>
                        <option value="Tiefling">Tiefling</option>
                        <option value="Half-Elf">Half-Elf</option>
                        <option value="Half-Orc">Half-Orc</option>
                        <option value="Gnome">Gnome</option>
                    </select>
                    <small class="help-text">Race provides ability bonuses and special traits</small>
                </div>

                <div class="form-group">
                    <label for="char-level">Level</label>
                    <input
                        type="number"
                        id="char-level"
                        value="1"
                        min="1"
                        max="5"
                    />
                    <small class="help-text">Starting level (1-5 recommended for balanced gameplay)</small>
                </div>
            </section>

            <!-- Personality & Background -->
            <section class="form-section">
                <h2>Personality & Background</h2>

                <div class="form-group">
                    <label for="char-personality">Personality Traits *</label>
                    <textarea
                        id="char-personality"
                        rows="3"
                        required
                        placeholder="Describe your character's personality in 2-3 sentences. Examples:
- Brave and loyal, always ready to defend allies
- Curious and mischievous, loves solving puzzles
- Stoic and disciplined, values honor above all"
                    ></textarea>
                    <small class="help-text">These traits will guide the AI in roleplaying your character</small>
                </div>

                <div class="form-group">
                    <label for="char-background">Background Story *</label>
                    <textarea
                        id="char-background"
                        rows="5"
                        required
                        placeholder="Write a brief backstory (1-2 paragraphs). Examples:
- Where does your character come from?
- What significant events shaped their life?
- Why are they adventuring?
- What are their goals or motivations?"
                    ></textarea>
                    <small class="help-text">This will be expanded by AI into a rich background</small>
                </div>
            </section>

            <!-- Actions -->
            <div class="form-actions">
                <button type="button" id="btn-cancel" class="btn-secondary">
                    Cancel
                </button>
                <button type="submit" id="btn-generate" class="btn-primary">
                    🎲 Generate Character
                </button>
            </div>
        </form>

        <!-- Loading State -->
        <div id="loading-state" class="hidden">
            <div class="spinner"></div>
            <p>Generating your character...</p>
            <small>This may take 5-10 seconds</small>
        </div>

        <!-- Character Preview -->
        <div id="character-preview" class="hidden">
            <h2>Character Generated!</h2>
            <div id="preview-content"></div>

            <div class="preview-actions">
                <button id="btn-regenerate" class="btn-secondary">
                    🔄 Regenerate
                </button>
                <button id="btn-save-character" class="btn-primary">
                    ✅ Save & Use Character
                </button>
            </div>
        </div>
    </div>

    <script src="character_creator.js"></script>
</body>
</html>
```

**File**: `src/ui/frontend/character_creator.js` (NUOVO)

```javascript
document.getElementById('character-form').addEventListener('submit', async (e) => {
    e.preventDefault()

    const formData = {
        name: document.getElementById('char-name').value,
        class: document.getElementById('char-class').value,
        race: document.getElementById('char-race').value,
        level: parseInt(document.getElementById('char-level').value),
        personality: document.getElementById('char-personality').value,
        background: document.getElementById('char-background').value
    }

    // Show loading
    document.getElementById('character-form').classList.add('hidden')
    document.getElementById('loading-state').classList.remove('hidden')

    try {
        const response = await fetch('/api/characters/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        })

        const result = await response.json()

        if (result.status === 'success') {
            showCharacterPreview(result.character)
        } else {
            showError(result.error || 'Character generation failed')
        }
    } catch (error) {
        console.error('Error:', error)
        showError('Network error. Please try again.')
    } finally {
        document.getElementById('loading-state').classList.add('hidden')
    }
})

function showCharacterPreview(character) {
    const previewContent = document.getElementById('preview-content')
    previewContent.innerHTML = `
        <div class="character-sheet">
            <h3>${character.name}</h3>
            <p class="subtitle">Level ${character.level} ${character.race} ${character.class}</p>

            <div class="stat-block">
                <h4>Ability Scores</h4>
                <div class="abilities">
                    <div>STR: ${character.abilities.strength}</div>
                    <div>DEX: ${character.abilities.dexterity}</div>
                    <div>CON: ${character.abilities.constitution}</div>
                    <div>INT: ${character.abilities.intelligence}</div>
                    <div>WIS: ${character.abilities.wisdom}</div>
                    <div>CHA: ${character.abilities.charisma}</div>
                </div>
            </div>

            <div class="stat-block">
                <h4>Skills</h4>
                <p>${character.skills.join(', ')}</p>
            </div>

            <div class="stat-block">
                <h4>HP & AC</h4>
                <p>Hit Points: ${character.hp_max} | Armor Class: ${character.ac}</p>
            </div>

            <div class="stat-block">
                <h4>Equipment</h4>
                <ul>
                    ${character.equipment.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>

            <div class="stat-block">
                <h4>Personality</h4>
                <p>${character.personality}</p>
            </div>

            <div class="stat-block">
                <h4>Background</h4>
                <p>${character.background}</p>
            </div>
        </div>
    `

    document.getElementById('character-preview').classList.remove('hidden')
}
```

---

### 3.2 LLM Character Generator

**File**: `src/agents/character_generator.py` (NUOVO)

#### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class AbilityScores(BaseModel):
    strength: int = Field(ge=8, le=15)
    dexterity: int = Field(ge=8, le=15)
    constitution: int = Field(ge=8, le=15)
    intelligence: int = Field(ge=8, le=15)
    wisdom: int = Field(ge=8, le=15)
    charisma: int = Field(ge=8, le=15)

class CharacterSheet(BaseModel):
    name: str
    class_name: str = Field(alias="class")
    race: str
    level: int = Field(ge=1, le=20)
    abilities: AbilityScores
    skills: List[str] = Field(min_items=3, max_items=6)
    equipment: List[str] = Field(min_items=3, max_items=10)
    hp_max: int = Field(gt=0)
    ac: int = Field(ge=10, le=20)
    spells: Optional[List[str]] = None  # Solo per caster
    personality: str = Field(min_length=100, max_length=500)
    background: str = Field(min_length=200, max_length=800)
```

#### Generator Implementation

```python
from datapizza.clients.openai import OpenAIClient
from src.config import OPENAI_API_KEY

class CharacterGenerator:
    def __init__(self):
        self.client = OpenAIClient(
            api_key=OPENAI_API_KEY,
            model="gpt-4o-mini",
            temperature=0.7
        )

    async def generate(self, form_data: dict) -> CharacterSheet:
        """
        Generate complete character sheet from user input.

        Args:
            form_data: {
                'name': str,
                'class': str,
                'race': str,
                'level': int,
                'personality': str (user input, 2-3 sentences),
                'background': str (user input, 1-2 paragraphs)
            }

        Returns:
            CharacterSheet with all fields populated
        """
        prompt = self._build_generation_prompt(form_data)

        response = await self.client.a_structured_response(
            input=prompt,
            output_cls=CharacterSheet,
            system_prompt=self._get_system_prompt()
        )

        character = response.structured_data[0]
        return character

    def _get_system_prompt(self) -> str:
        return """You are an expert D&D 5e character creator.

Your task is to generate a complete, balanced character sheet that follows official D&D 5e rules.

RULES TO FOLLOW:
1. Ability Scores:
   - Use standard array (15, 14, 13, 12, 10, 8)
   - Assign based on class optimization (e.g., Fighter needs high STR, Wizard needs high INT)
   - Apply racial bonuses according to D&D 5e rules

2. Skills:
   - Select 3-4 skills appropriate for class + background
   - Only choose from skills the class can have
   - Consider personality when choosing

3. Equipment:
   - Follow Player's Handbook starting equipment for the class
   - Level 1: basic gear only (no magic items)
   - Levels 2-5: may have one uncommon magic item

4. Hit Points:
   - Level 1: class hit die max + CON modifier
   - Higher levels: average per level (class hit die / 2 + 1) + CON modifier

5. Armor Class:
   - Based on armor type + DEX modifier
   - Consider class proficiencies

6. Spells (if caster):
   - Follow spell slots for class and level
   - Choose thematic spells based on personality

7. Personality & Background:
   - Expand user input into rich, coherent narrative
   - Keep tone consistent with character concept
   - Add depth without contradicting user input

CRITICAL: The character MUST be legal according to D&D 5e rules."""

    def _build_generation_prompt(self, form_data: dict) -> str:
        return f"""Generate a D&D 5e character sheet with these specifications:

**Basic Info:**
- Name: {form_data['name']}
- Class: {form_data['class']}
- Race: {form_data['race']}
- Level: {form_data['level']}

**User-Provided Personality:**
{form_data['personality']}

**User-Provided Background:**
{form_data['background']}

**Generate:**
1. Optimized ability scores (standard array + racial bonuses)
2. Appropriate skills (3-4 skills for class + background)
3. Starting equipment (follow PHB for {form_data['class']})
4. Calculated HP (class hit die + CON modifier)
5. Armor Class (based on equipment)
6. {"Spell list (appropriate for level)" if self._is_caster(form_data['class']) else "No spells needed"}
7. Expanded personality (5-6 sentences building on user input)
8. Expanded background (300-500 words, rich narrative integrating user backstory)

Ensure all values are legal and balanced for D&D 5e level {form_data['level']}."""

    def _is_caster(self, class_name: str) -> bool:
        caster_classes = ['Wizard', 'Cleric', 'Druid', 'Warlock', 'Sorcerer', 'Bard', 'Paladin', 'Ranger']
        return class_name in caster_classes
```

---

### 3.3 Validation Layer

**File**: `src/validation/character_validator.py` (NUOVO)

#### D&D 5e Rules Validation

```python
from src.agents.character_generator import CharacterSheet

class CharacterValidator:
    """Validates CharacterSheet against D&D 5e rules"""

    STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

    CLASS_SKILLS = {
        'Fighter': ['Acrobatics', 'Animal Handling', 'Athletics', 'History', 'Insight', 'Intimidation', 'Perception', 'Survival'],
        'Wizard': ['Arcana', 'History', 'Insight', 'Investigation', 'Medicine', 'Religion'],
        'Rogue': ['Acrobatics', 'Athletics', 'Deception', 'Insight', 'Intimidation', 'Investigation', 'Perception', 'Performance', 'Persuasion', 'Sleight of Hand', 'Stealth'],
        'Cleric': ['History', 'Insight', 'Medicine', 'Persuasion', 'Religion'],
        # ... add all classes
    }

    CLASS_HIT_DICE = {
        'Barbarian': 12,
        'Fighter': 10,
        'Paladin': 10,
        'Ranger': 10,
        'Cleric': 8,
        'Rogue': 8,
        'Wizard': 6,
        # ... add all classes
    }

    def validate(self, character: CharacterSheet) -> tuple[bool, List[str]]:
        """
        Validate character sheet.

        Returns:
            (is_valid, errors_list)
        """
        errors = []

        errors.extend(self._validate_ability_scores(character.abilities))
        errors.extend(self._validate_skills(character.skills, character.class_name))
        errors.extend(self._validate_hp(character.hp_max, character.level, character.class_name, character.abilities))
        errors.extend(self._validate_ac(character.ac))

        return (len(errors) == 0, errors)

    def _validate_ability_scores(self, abilities: AbilityScores) -> List[str]:
        """Ensure ability scores use standard array"""
        errors = []

        scores = [
            abilities.strength,
            abilities.dexterity,
            abilities.constitution,
            abilities.intelligence,
            abilities.wisdom,
            abilities.charisma
        ]

        # Allow for racial bonuses (+2, +1 typical)
        # Check if scores are reasonable (8-17 range with bonuses)
        for score in scores:
            if score < 8 or score > 17:
                errors.append(f"Ability score {score} out of valid range (8-17 with racial bonuses)")

        # Sum should be close to standard array sum (73) + racial bonuses (~3)
        total = sum(scores)
        if total < 73 or total > 79:
            errors.append(f"Ability score total {total} suspicious (expected 73-79)")

        return errors

    def _validate_skills(self, skills: List[str], class_name: str) -> List[str]:
        """Ensure skills are valid for class"""
        errors = []

        allowed_skills = self.CLASS_SKILLS.get(class_name, [])

        for skill in skills:
            if skill not in allowed_skills:
                errors.append(f"Skill '{skill}' not available for {class_name}")

        return errors

    def _validate_hp(self, hp: int, level: int, class_name: str, abilities: AbilityScores) -> List[str]:
        """Validate HP calculation"""
        errors = []

        hit_die = self.CLASS_HIT_DICE.get(class_name, 8)
        con_mod = (abilities.constitution - 10) // 2

        # Level 1: max hit die + CON mod
        # Higher levels: average per level + CON mod
        if level == 1:
            expected_hp = hit_die + con_mod
        else:
            avg_per_level = (hit_die // 2) + 1
            expected_hp = hit_die + con_mod + (avg_per_level + con_mod) * (level - 1)

        # Allow +/- 2 tolerance
        if abs(hp - expected_hp) > 2:
            errors.append(f"HP {hp} doesn't match expected {expected_hp} for level {level} {class_name}")

        return errors

    def _validate_ac(self, ac: int) -> List[str]:
        """Validate armor class is reasonable"""
        errors = []

        if ac < 10 or ac > 20:
            errors.append(f"AC {ac} out of reasonable range (10-20)")

        return errors
```

---

### 3.4 Backend API Endpoints

**File**: `src/ui/server.py` (MODIFICA)

#### Character Creation Endpoint

```python
from fastapi import HTTPException
from src.agents.character_generator import CharacterGenerator, CharacterSheet
from src.validation.character_validator import CharacterValidator
import yaml
from pathlib import Path

character_generator = CharacterGenerator()
character_validator = CharacterValidator()

@app.post("/api/characters/create")
async def create_character(form_data: dict):
    """
    Generate and validate character from user input.

    Returns:
        {
            "status": "success",
            "character": CharacterSheet,
            "file": "path/to/saved/yaml"
        }
    """
    try:
        # Generate character with LLM
        character = await character_generator.generate(form_data)

        # Validate against D&D 5e rules
        is_valid, errors = character_validator.validate(character)

        if not is_valid:
            # Retry generation with corrective prompt (max 3 attempts)
            attempt = 0
            while not is_valid and attempt < 3:
                attempt += 1
                print(f"Validation failed (attempt {attempt}): {errors}")

                # Regenerate with error feedback
                character = await character_generator.generate(
                    form_data,
                    previous_errors=errors
                )
                is_valid, errors = character_validator.validate(character)

            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Character generation failed validation: {errors}"
                )

        # Save to YAML
        char_file = Path(f"data/characters/custom_{character.name.replace(' ', '_')}.yaml")
        char_file.parent.mkdir(parents=True, exist_ok=True)

        with open(char_file, 'w') as f:
            yaml.dump(character.dict(), f)

        return {
            "status": "success",
            "character": character.dict(),
            "file": str(char_file)
        }

    except Exception as e:
        print(f"Character creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/characters")
async def list_characters():
    """List all available characters (default + custom)"""
    char_dir = Path("data/characters")
    characters = []

    for yaml_file in char_dir.glob("*.yaml"):
        with open(yaml_file) as f:
            char = yaml.safe_load(f)

        characters.append({
            "name": char['name'],
            "class": char.get('class_name', char.get('class')),
            "race": char['race'],
            "level": char['level'],
            "file": str(yaml_file),
            "is_custom": yaml_file.name.startswith('custom_')
        })

    return {"characters": characters}


@app.get("/api/characters/{name}")
async def get_character(name: str):
    """Get full character sheet for preview"""
    char_file = Path(f"data/characters/{name}.yaml")

    if not char_file.exists():
        # Try custom_ prefix
        char_file = Path(f"data/characters/custom_{name}.yaml")

    if not char_file.exists():
        raise HTTPException(status_code=404, detail="Character not found")

    with open(char_file) as f:
        character = yaml.safe_load(f)

    return {"character": character}


@app.delete("/api/characters/{name}")
async def delete_character(name: str):
    """Delete custom character"""
    char_file = Path(f"data/characters/custom_{name}.yaml")

    if not char_file.exists():
        raise HTTPException(status_code=404, detail="Character not found")

    if not char_file.name.startswith('custom_'):
        raise HTTPException(status_code=403, detail="Cannot delete default characters")

    char_file.unlink()
    return {"status": "deleted"}
```

---

### 3.5 Integration con Lobby

**File**: `src/ui/frontend/lobby.html` (MODIFICA)

#### Character Selection con Gallery

```html
<!-- Character Selector per ogni Player Slot -->
<div class="player-slot">
    <h3>Player 1 (Human)</h3>

    <div class="character-selector">
        <select id="char-select-1" class="char-dropdown">
            <option value="">-- Select Character --</option>
            <!-- Populated dynamically from /api/characters -->
        </select>

        <button class="btn-icon" onclick="previewCharacter(1)" title="Preview">
            👁️
        </button>

        <button class="btn-icon" onclick="openCharacterCreator()" title="Create New">
            ➕
        </button>
    </div>
</div>

<!-- Character Preview Modal -->
<div id="preview-modal" class="modal hidden">
    <div class="modal-content">
        <span class="close" onclick="closePreview()">&times;</span>
        <div id="preview-body"></div>
    </div>
</div>
```

**File**: `src/ui/frontend/lobby.js` (MODIFICA)

```javascript
async function loadCharacters() {
    const response = await fetch('/api/characters')
    const data = await response.json()

    const selects = document.querySelectorAll('.char-dropdown')
    selects.forEach(select => {
        select.innerHTML = '<option value="">-- Select Character --</option>'

        data.characters.forEach(char => {
            const option = document.createElement('option')
            option.value = char.file
            option.textContent = `${char.name} (${char.class} ${char.level})`
            if (char.is_custom) {
                option.textContent += ' ⭐'
            }
            select.appendChild(option)
        })
    })
}

async function previewCharacter(slot) {
    const select = document.getElementById(`char-select-${slot}`)
    const charFile = select.value

    if (!charFile) return

    const charName = charFile.split('/').pop().replace('.yaml', '')
    const response = await fetch(`/api/characters/${charName}`)
    const data = await response.json()

    showCharacterPreview(data.character)
}

function openCharacterCreator() {
    window.open('character_creator.html', '_blank')
}
```

---

## File da Creare/Modificare

### Nuovi File
| File | LOC | Descrizione |
|------|-----|-------------|
| `src/agents/character_generator.py` | ~180 | LLM-based character generation |
| `src/validation/character_validator.py` | ~120 | D&D 5e rules validation |
| `src/ui/frontend/character_creator.html` | ~180 | Character creation UI |
| `src/ui/frontend/character_creator.js` | ~100 | Form handling + preview |

### File da Modificare
| File | LOC Aggiunte | Descrizione |
|------|--------------|-------------|
| `src/ui/server.py` | ~180 | API endpoints (create, list, get, delete) |
| `src/ui/frontend/lobby.html` | ~80 | Character selector + preview modal |
| `src/ui/frontend/lobby.js` | ~60 | Load characters, preview logic |
| `src/ui/frontend/style.css` | ~80 | Styling creator + modal |

**Totale**: ~980 righe (~580 nuove + ~400 modifiche)

---

## Deliverables

### Funzionalità Complete
- ✅ Character Creator UI con form completo
- ✅ LLM-based generation (AI genera stats, skills, equipment)
- ✅ Validation layer (garantisce conformità D&D 5e)
- ✅ Character gallery nella lobby (default + custom)
- ✅ Character preview modal (full stats display)
- ✅ CRUD API endpoints (create, list, get, delete)
- ✅ YAML persistence per custom characters
- ✅ Retry logic (max 3 tentativi se validation fallisce)

### Test Coverage
- ✅ Test character generation (varie classi e razze)
- ✅ Test validation (invalid ability scores, skills, HP)
- ✅ Test API endpoints (create, list, get, delete)
- ✅ Test integration con lobby (select → preview → play)
- ✅ Test edge cases (duplicate names, invalid input)

### User Experience
- ✅ Intuitive form con help text
- ✅ Loading indicator durante generation (5-10s)
- ✅ Rich preview con full character sheet
- ✅ Option to regenerate if unhappy con result
- ✅ Clear error messages se validation fallisce

---

## Rischi e Mitigazioni

### Rischio 1: LLM Genera Character Invalido
**Mitigazione**: Validation layer + retry logic (max 3 attempts) con error feedback

### Rischio 2: Ability Scores Non Bilanciati
**Mitigazione**: System prompt enfatizza standard array, validator controlla sum

### Rischio 3: Equipment Overpowered per Level
**Mitigazione**: Validator blocca magic items per level 1, limita rarità per levels 2-5

### Rischio 4: User Input Confuso o Conflittuale
**Mitigazione**: Help text nel form, examples placeholder, AI interpreta best effort

### Rischio 5: Performance (generation ~5-10s)
**Mitigazione**: Loading indicator, async generation, user può continuare browsing

---

## Passaggio alla Phase 04

Una volta completata Phase 03, gli utenti potranno creare **personaggi personalizzati** con assistenza AI, garantendo conformità alle regole D&D 5e.

La **Phase 04** si concentrerà su **Integration & Testing** per validare tutte le feature implementate nelle Phases 01-03:
- End-to-end testing (human player + voice + custom character)
- Performance validation
- UI/UX polish
- Bug fixing
- Final documentation
