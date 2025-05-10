# ================================================================
#  entities.py  (engine‑agnostic reference classes)
# ================================================================
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence

# ----------------------------------------------------------------
#  ENUMS (expressed as str literals to avoid importing Enum class)
# ----------------------------------------------------------------
EVENTS        = {"OnStart","EveryFrame","OnTimer","OnCollision",
                 "OnVoiceCommand","OnHealthBelow","OnDestroyed"}
ENTITY_TYPES  = {"character","projectile","hazard","powerup","effect"}
COMPONENTS    = {"Transform","Sprite","Collider","RigidBody","Health",
                 "Damage","AI_Brain","Lifespan","ParticleEmitter",
                 "AudioCue","CustomVar"}

# ----------------------------------------------------------------
#  ACTION BASE ‑‑ each subclass must implement do(engine_ctx, self_ent, target)
# ----------------------------------------------------------------
class Action:
    def do(self, eng, self_ent:'Entity', target:Any|None): ...

# Pure‑data subclasses ---------------------------------------------------------
@dataclass
class SpawnAction(Action):
    prefab:str; x:Any; y:Any; properties:Dict[str,Any]|None=None
@dataclass
class ApplyForceAction(Action):
    vector:Dict[str,Any]           # {"x":expr,"y":expr}
@dataclass
class ModifyStatAction(Action):
    field:str; value:Any; target:str|"self"|None="self"
@dataclass
class PlayAnimationAction(Action):
    name:str
@dataclass
class PlaySoundAction(Action):
    cue:str
@dataclass
class DestroyAction(Action):
    pass
@dataclass
class SetTimerAction(Action):
    id:str; duration:float; repeat:int=0
@dataclass
class CommentaryAction(Action):
    text:str

ACTION_MAP:Dict[str,type[Action]] = {
    "Spawn":SpawnAction,
    "ApplyForce":ApplyForceAction,
    "ModifyStat":ModifyStatAction,
    "PlayAnimation":PlayAnimationAction,
    "PlaySound":PlaySoundAction,
    "Destroy":DestroyAction,
    "SetTimer":SetTimerAction,
    "Commentary":CommentaryAction,
}

# ----------------------------------------------------------------
#  BEHAVIOR
# ----------------------------------------------------------------
@dataclass
class Behavior:
    event:str                       # must be in EVENTS
    actions:Sequence[Action]

# ----------------------------------------------------------------
#  ENTITY (engine‑agnostic)
# ----------------------------------------------------------------
@dataclass
class Entity:
    id:str
    prefab:str                      # must be in ENTITY_TYPES
    components:Dict[str,Any] = field(default_factory=dict)
    behaviors:List[Behavior] = field(default_factory=list)
    engine_obj:Any=None             # opaque handle set by adapter

    # Adapter hook -------------------------------------------------
    def build(self, engine_ctx, prefab_factory:Callable[...,Any]):
        """Instantiate engine object via prefab_factory then let the
           adapter apply components and wire events."""
        self.engine_obj = prefab_factory(self.prefab, self.components)

# ----------------------------------------------------------------
#  TIMER
# ----------------------------------------------------------------
@dataclass
class Timer:
    id:str
    duration:float
    repeat:int
    on_complete:Sequence[Action]

# ----------------------------------------------------------------
#  PACKET  (the top‑level MOD packet)
# ----------------------------------------------------------------
@dataclass
class ModPacket:
    entities:List[Entity]
    timers:List[Timer]

    @classmethod
    def from_dict(cls, d:Dict[str,Any]) -> 'ModPacket':
        ents=[]
        for e in d.get("entities",[]):
            beh=[]
            for b in e.get("behaviors",[]):
                acts=[ACTION_MAP[a["type"]](**{k:v for k,v in a.items() if k!="type"})
                      for a in b["actions"]]
                beh.append(Behavior(event=b["event"], actions=acts))
            ents.append(Entity(id=e["id"], prefab=e["prefab"],
                               components=e.get("components",{}),
                               behaviors=beh))
        timers=[]
        for t in d.get("timers",[]):
            acts=[ACTION_MAP[a["type"]](**{k:v for k,v in a.items() if k!="type"})
                  for a in t["on_complete"]]
            timers.append(Timer(id=t["id"], duration=t["duration"],
                                repeat=t.get("repeat",0), on_complete=acts))
        return cls(entities=ents, timers=timers)
    
# ----------------------------------------------------------------
# Adapter methods for connecting the above to the rest of the codebase
# ----------------------------------------------------------------

# 1. convert prefab → actual Sprite / Fighter / Projectile
def prefab_factory(prefab_name:str, components:dict):
    if prefab_name == "projectile":
        return ProjectileSprite(**components)
    if prefab_name == "hazard":
        return SpikeSprite(**components)
    ...

# 2. execute actions
def action_runner(action:Action, engine_ctx, self_ent, target):
    if isinstance(action, SpawnAction):
        spawn_entity(action.prefab,
                     evaluate(action.x,self_ent,target),
                     evaluate(action.y,self_ent,target),
                     action.properties or {})
    elif isinstance(action, ApplyForceAction):
        vec = action.vector
        apply_force(self_ent.engine_obj,
                    evaluate(vec["x"],self_ent,target),
                    evaluate(vec["y"],self_ent,target))
    ...

# 3. wire USS events to EventGraph
def on_collision(self_sprite, other_sprite):
    DSL.process_event("OnCollision", ctx={"target":sprite_to_entity(other_sprite)})

