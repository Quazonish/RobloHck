--VER 2.0.1

--[[
TODO:
add pinfo
add flashback

]]

--locals

local http = game:GetService("HttpService")
local betteriy = {
  PluginName = "Infinite Yield+",
  PluginDescription = "Epic ain't it? 😎",
  Commands = setmetatable({},{__call = function(self,name,args)
    self[name] = {
      ListName = (args.name or name)..(args.addtoname or ""),
      Description = args.desc or "No description available",
      Function = args.func or function() end, --set a blank function so that the plugin still loads even if there was no function on the cmd
      Aliases = args.aliases or {}
    }
  end})
}
local addcmd = betteriy.Commands
local LP = Players.LocalPlayer
local RS = game:GetService("RunService")
local connections = {}
local contypes = {
    Stepped = RS.Stepped,
    RenderStepped = RS.RenderStepped,
    Heartbeat = RS.Heartbeat
}

--functions

local function readsave(key)
  local save = http:JSONDecode(readfile("IY_FE.iy"))
  if key ~= nil then
    return save[key]
  end
  return save
end

local function writesave(key,value)
  if key ~= nil and value ~= nil then
    local save = http:JSONDecode(readfile("IY_FE.iy"))
    save[key] = value
    writefile("IY_FE.iy", http:JSONEncode(save))
  else
    notify('Invalid key/value specified to writesave')
  end
end

local function getchar(plr)
  return plr and (plr.Character or plr.CharacterAdded:Wait()) or LP.Character or LP.CharacterAdded:Wait()
end

local function gethrp(plr,gettorso)
	local char = getchar(plr)
	local hrp,torso = char:FindFirstChild("HumanoidRootPart"),char:FindFirstChild("Torso") or char:FindFirstChild("UpperTorso")
	return (gettorso and torso) or (hrp and (torso and (torso.Position-hrp.Position).Magnitude<1) and hrp) or torso or char.PrimaryPart or char:FindFirstChildWhichIsA("BasePart")
end

local function gethum(plr,wait)
  local chr = getchar(plr)
  local hum = chr:FindFirstChildWhichIsA("Humanoid")
  if hum then return hum end
  if wait then
    repeat
      local h = chr.ChildAdded:Wait()
      if h:IsA("Humanoid") then
        hum = h
      end
    until hum
  end
end

local function bind(name,signal,f,...)
    assert(typeof(signal)=="RBXScriptSignal" or contypes[signal],string.format("Invalid step type (valid types are %s)",(function() local r = "" for n,_ in pairs(contypes) do r=r..tostring(n)..", " end return r:sub(1,-2) end)()))
    assert(type(name)=="string","Binded name must be a string!")
    assert(type(f)=="function","argument 3 is not a function!")
    signal = contypes[signal] or signal
    local args = {...}
    local con = signal:Connect(function(...) f(...,unpack(args)) end)
    if not connections[name] then
        connections[name] = {}
    end
    table.insert(connections[name],con)
end

local function unbind(name)
    assert(type(name)=="string","argument is not a string!")
    local t,num = connections[name],0
    if t then
        num=#t
        for _,con in pairs(t) do
            con:Disconnect()
        end
        connections[name] = {}
    end
    return num
end

local function stare(plr)
  bind("StareFunc","RenderStepped",function()
    local hrp,hrp2 = gethrp(),gethrp(plr)
    hrp.CFrame = CFrame.new(hrp.Position, hrp2.Position)
  end)
end

local function unstare()
  unbind("StareFunc")
end

local history = readsave("cmdHistory")
if history then
  if #cmdHistory>0 then
    for i=#history,1,-1 do
      table.insert(cmdHistory,1,history[i])
    end
  else
    cmdHistory = history
  end
end

setmetatable(cmdHistory,{__newindex = function(self,k,v) rawset(self,k,v) writesave("cmdHistory",self) end})

bind("PrefixFix",Cmdbar.Focused,function()
  repeat
    Cmdbar.Text = ""
    RunService.RenderStepped:Wait()
  until Cmdbar.Text == ""
end)

local function sayaboutplayer(plr,isinsult)
  local chat = game:GetService("ReplicatedStorage"):FindFirstChild("DefaultChatSystemChatEvents")
  local say = chat and chat:FindFirstChild("SayMessageRequest")
  if not chat or not say then notify("Chat system not found") end
  local insults = {
    "%s's mom is so fat that she generates her own gravity field",
    "my grandma has more skill than you",
    "imagine being %s right now",
    "%s's stench is so bad I can smell it over the internet'",
    "Rich items don't grant you actual fame, %s",
    "... The reason I am so silent is because you look so ugly.",
    "%s you have two parts of your brain, 'left' and 'right'. In the left side, there's nothing right. In the right side, there's nothing left.",
    "Two wrongs don't make a right, take your parents as an example.",
    "I would roast you %s but I don't engage in mental combat with the unarmed.",
    "%s, I'm not insulting you. I'm describing you.",
    "I don't think %s is stupid. he/she just has bad luck when thinking.",
    "%s, it looks like your face caught on fire and someone tried to put it out with a hammer.",
    "%s, you have something on your chin... no, the 3rd one down.",
    "%s, brains aren't everything. In your case they're nothing.",
    "Aww, it's so cute when you try to talk about things you don't understand.",
    "The human brain is one of the most complex objects in the universe. Is it any wonder that %s never learned how to use it.",
    "Roses are red, Violets are blue. I've got five fingers, The middle one is for you.",
    "%s, You're so sad that even Bob the Builder can't fix your life.",
    " I can feel my personality turning a dull shade of grey when I talk to %s",
    "I had prepared for a battle of wits but I see you came unarmed, %s",
    "Sorry I didn't respond to you just now. I was doing something productive and not wasting my precious time with your lowlife speeches.",
    "%s, You're so dense, light must bend around you.",
    "%s, you look like something I drew with my left hand.",
    "Staring at the sun without sunglasses is much less painful than looking at %s's face.",
    "Looking at %s, I understand why some animals eat their young."
  }
  local compliments = {
    "%s is the coolest person in this server!",
    "I wish %s would play with me everyday!",
    "OMGOMGOMG %s IS IN MY GAME OMG OMG OMG OMG!!!",
    "I wish I could be more like %s",
    "Will you dayte me %s?",
    "I want %s to come over and play some games with me!",
    "%s will you accept my friend request please?",
    "%s, I really like your avatar!",
    "%s, I really want to be your friend!",
    "%s is truly amazing. Truly!",
    "%s is incredible!",
    "%s, you are my favourite here!!",
    "%s, I am complimenting you right now at this very moment.",
    "%s you are really awesome",
    "%s when will you be my friend!?",
    "%s is such a great person",
    "%s is a fantastic person!"
  }
  local t = isinsult and insults or compliments
  say:FireServer(t[math.random(1,#t)]:format(plr),"All")
end

addcmd("compliment",{
  addtoname = " [plr]",
  desc = "compliments [plr]",
  func = function(plrs,speaker)
    for _,name in pairs(getPlayer(plrs[1], speaker)) do
      if name ~= speaker.Name then
        sayaboutplayer(Players[name].DisplayName)
      end
    end
  end
})

addcmd("insult",{
  addtoname = " [plr]",
  desc = "insults [plr]",
  func = function(plrs,speaker)
    for _,name in pairs(getPlayer(plrs[1], speaker)) do
      if name ~= speaker.Name then
        sayaboutplayer(Players[name].DisplayName,true)
      end
    end
  end
})

addcmd("follow",{
  addtoname = " [plr] [dist]",
  desc = "follows [plr] at [dist]",
  func = function(args,speaker)
    local plr = getPlayer(args[1], speaker)
    plr = Players[plr[1]]
    if not plr then notify("No player specified") return end
    local function follow(_,plr)
      local cf = gethrp(plr).CFrame
      local hum = gethum()
      if hum and hum.Sit then hum.Sit = false end
      gethrp().CFrame = cf + cf.lookVector * (args[2] and tonumber(args[2]) or -5)
    end
    bind("FollowFunc","Heartbeat",follow,plr)
  end
})

addcmd("unfollow",{
  desc = "stops following people",
  func = function(plrs,speaker)
    unbind("FollowFunc")
  end
})

addcmd("rejoinrefresh",{
  addtoname = "/rjre",
  desc = "rejoins the game to your last position and re-executes iy",
  aliases = {"rjre"},
  func = function()
    if not DONE then
      DONE = true
      local qot = game:HttpGet('https://raw.githubusercontent.com/EdgeIY/infiniteyield/master/source')
      local hrp = LP.Character and LP.Character:FindFirstChild("HumanoidRootPart")
      if hrp then
        qot = "task.spawn(function() "..qot.." end) repeat wait() until game and game:IsLoaded() local lp = game:GetService('Players').LocalPlayer local char = lp.Character or lp.CharacterAdded:Wait() repeat char:WaitForChild('HumanoidRootPart').CFrame = CFrame.new("..tostring(hrp.CFrame)..") wait() until (Vector3.new("..tostring(hrp.Position)..") - char:WaitForChild('HumanoidRootPart').Position).Magnitude < 10"
      end
      queueteleport(qot)
      game:GetService("TeleportService"):TeleportCancel()
      execCmd("rejoin")
    end
  end
})

addcmd("freezecam",{
  desc = "freezes your camera in place",
  func = function()
    workspace.CurrentCamera.CameraType = Enum.CameraType.Fixed
  end
})

addcmd("orbit",{
  addtoname = " [plr]",
  desc = "orbits torwards [plr]",
  func = function(args,speaker)
    local plr = getPlayer(args[1], speaker)
    plr = plr[1] and Players[plr[1]]
    local hum = gethum()
    local hum2 = gethum(plr)

    local function rocket(plr)
      gethum(LP,true).Sit = true
      local l = Instance.new("RocketPropulsion")
      l.CartoonFactor = 1
      l.MaxThrust = 5000
      l.MaxSpeed = 100
      l.ThrustP = 5000
      l.Name = "OrbitMove"
      l.Target = gethrp(plr)
      l.Parent = gethrp()
      l:Fire()
    end

    if plr and hum and hum2 then
      rocket(plr)
      bind("Orbit",hum.Died,function() execCmd("unorbit") plr.CharacterAdded:Wait() execCmd("orbit "..plr.Name) end)
      bind("Orbit",hum2.Died,function() execCmd("unorbit") plr.CharacterAdded:Wait() execCmd("orbit "..plr.Name) end)
      bind("Orbit",hum.Seated,function(sit) if not sit then execCmd("unorbit") end end)
    end
  end
})

addcmd("orbit2",{
  addtoname = " [plr] [speed] [offset x, y, z]",
  desc = "orbits around [plr]",
  func = function(args,speaker)
    local plr = getPlayer(args[1], speaker)
    plr = plr[1] and Players[plr[1]]
    local hum = gethum()
    local hum2 = gethum(plr)
    local oldnotify = notify
    notify = function() notify = oldnotify end
    execCmd("view "..plr.Name)
    local offset = Vector3.new(args[3] or 6,args[4] or 0,args[5] or 0)
    local rotstep = 0
    local function step()
         rotstep = rotstep + (args[2] or 2)
         gethrp().CFrame = CFrame.new(gethrp(plr).Position) * CFrame.Angles(0,math.rad(rotstep),0) * CFrame.new(offset)
    end
    hum.Sit = true
    stare(plr)
    bind("Orbit","Heartbeat",step)
    bind("Orbit",hum.Died,function() execCmd("unorbit") plr.CharacterAdded:Wait() execCmd("orbit2 "..table.concat(args," ")) end)
    bind("Orbit",hum2.Died,function() execCmd("unorbit") plr.CharacterAdded:Wait() execCmd("orbit2 "..table.concat(args," ")) end)
    bind("Orbit",hum.Seated,function(sit) if not sit then execCmd("unorbit") end end)
  end
})

addcmd("unorbit",{
  addtoname = "/noorbit",
  desc = "stops orbiting",
  aliases = {"noorbit"},
  func = function()
    unbind("Orbit")
    unstare()
    local oldnotify = notify --iy is gay and doesn't have a nonotify for view
    notify = function() notify = oldnotify end
    execCmd("unview")
    local hrp = gethrp()
    local orbit = hrp:FindFirstChild("OrbitMove")
    while orbit do
      orbit = hrp:FindFirstChild("OrbitMove")
      if orbit then orbit:Destroy() end
    end
  end
})

addcmd("trip",{
  addtoname = " [num]",
  desc = "trips your character for [num] length",
  func = function(args)
    local hrp = gethrp()
    local hum = gethum()
    local force = -10
    hum:ChangeState(Enum.HumanoidStateType.Physics)
    local body = Instance.new("BodyAngularVelocity")
    body.Parent = hrp
    body.AngularVelocity = Vector3.new(force,force,force)
    game:GetService("Debris"):AddItem(body,.1)
    local active = true
    bind("TrippinBalls",UserInputService.JumpRequest,function() if active then active = false hum:ChangeState(Enum.HumanoidStateType.GettingUp) unbind("TrippinBalls") end end)
    wait(args[1] and tonumber(args[1]) or 2)
    if active then
      active = false
      hum:ChangeState(Enum.HumanoidStateType.GettingUp)
    end
  end
})

addcmd("walk",{
  desc = "walks forward automatically",
  func = function(args,speaker)
    local plr = getPlayer(args[1], speaker)
    local hum = gethum()
    bind("Walk","Heartbeat",function() hum:MoveTo(gethrp().Position + gethrp().CFrame.lookVector * 4) end)
  end
})

addcmd("unwalk",{
  addtoname = "/nowalk",
  desc = "stops you from walking automatically",
  func = function()
    unbind("Walk")
  end
})

execCmd("removecmd nosit") --my version better
execCmd("removecmd unnosit")
wait()
addcmd("nosit",{
  addtoname = "/stopsit",
  desc = "stops you from being able to sit",
  aliases = {"stopsit"},
  func = function(args,speaker)
    gethum():SetStateEnabled(Enum.HumanoidStateType.Seated,false)
    bind("nosit",LP.CharacterAdded,function() gethum(LP,true):SetStateEnabled(Enum.HumanoidStateType.Seated,false) end)
  end
})

addcmd("unnosit",{
  addtoname = "/unstopsit",
  desc = "disables nosit/stopsit",
  aliases = {"unstopsit"},
  func = function(args,speaker)
    unbind("nosit")
    gethum():SetStateEnabled(Enum.HumanoidStateType.Seated,true)
  end
})

addcmd("inviscam",{
  addtoname = "/invisiblecam",
  desc = "Makes your camera go through objects always keeping the humanoid visible",
  aliases = {"invisiblecam"},
  func = function(args,speaker)
    LP.DevCameraOcclusionMode = Enum.DevCameraOcclusionMode.Invisicam
  end
})

addcmd("noinviscam",{
  addtoname = "/viscam",
  desc = "Changes the camera back to default behavior",
  aliases = {"noinvisiblecam","uninvisiblecam","viscam"},
  func = function(args,speaker)
    LP.DevCameraOcclusionMode = Enum.DevCameraOcclusionMode.Zoom
  end
})

addcmd("die",{
  addtoname = "/oof",
  desc = "make you suicide",
  aliases = {"oof"},
  func = function(args,speaker)
    local char = getchar()
    char:BreakJoints()
  end
})

addcmd("flip",{
  addtoname = "/fliptool",
  desc = "Gives you a tool that makes you do a 360 flip",
  aliases = {"fliptool"},
  func = function()
    local useps = true
    local LP=game:GetService("Players").LocalPlayer
    local chr=LP.Character
    local hum = chr:FindFirstChildWhichIsA("Humanoid")
    local t=Instance.new("Tool",LP.Backpack)
    t.Name="360"
    t.RequiresHandle=false
    local debounce=false
    local function _restoreproperties()
      local Torso = chr:FindFirstChild("Torso")
      local RightS = Torso and Torso:FindFirstChild("Right Shoulder") or chr.RightUpperArm:FindFirstChild("RightShoulder")
      local LeftS = Torso and Torso:FindFirstChild("Left Shoulder") or chr.LeftUpperArm:FindFirstChild("LeftShoulder")
      local RightH = Torso and Torso:FindFirstChild("Right Hip") or chr.RightUpperLeg:FindFirstChild("RightHip")
      local LeftH = Torso and Torso:FindFirstChild("Left Hip") or chr.LeftUpperLeg:FindFirstChild("LeftHip")
      if not RightS then return end
      RightS.MaxVelocity = .15
      LeftS.MaxVelocity = .15
      RightH.MaxVelocity = .1
      LeftH.MaxVelocity = .1
      RightS.DesiredAngle = 0
      LeftS.DesiredAngle = 0
      LeftH.DesiredAngle = 0
      RightH.DesiredAngle = 0
    end

    local function ManageAnimation(value)
      local Anim = chr:FindFirstChild("Animate")
      if not Anim then return end
      if value then
        Anim.Disabled = false
      else
        Anim.Disabled = true
      end
    end
    local function togglestates(enable)
        enable=enable and true or false
      local enum = Enum.HumanoidStateType
      for _,state in pairs(enum:GetEnumItems()) do
        if state ~= enum.Dead and state~= enum.None then
          hum:SetStateEnabled(state,(enable))
        end
      end
      ManageAnimation(enable)
    end

    local function Down(ml)
      for i=1, ml.velocity.y/3 do
        ml.velocity = ml.velocity+Vector3.new(0,-4.25,0)
        wait()
      end
      ml:Remove()
    end

    local function Flip()
      if debounce then return end
      debounce=true
      local Torso = chr:FindFirstChild("Torso") or chr.UpperTorso
      local CF = Torso.CFrame
      if not useps then
          togglestates()
      else
          hum.PlatformStand = true
      end
      local VelUp = Instance.new("BodyVelocity")
      VelUp.velocity = Vector3.new(0,50,0)+Torso.CFrame.lookVector*26 --Middle (0,0,0). Change for height.
      VelUp.P = VelUp.P*2
      VelUp.maxForce = Vector3.new(10000,10000,10000)*999
      VelUp.Parent = Torso
      coroutine.resume(coroutine.create(Down),VelUp)
      local Gyro = Instance.new("BodyGyro")
      Gyro.P = Gyro.P*10
      Gyro.maxTorque = Vector3.new(100000,100000,100000)*999
      Gyro.cframe = CF
      Gyro.Parent = Torso
      for i=1, 5 do --The amount of time your guy flips.
        Gyro.cframe = Gyro.cframe*CFrame.fromEulerAnglesXYZ(math.pi/-5,0,0) --The amount of flips. 1 = -16, 2 = -8
        wait()
      end
      wait()
      for i=1, 9 do --The amount of time your guy flips.
        Gyro.cframe = Gyro.cframe*CFrame.fromEulerAnglesXYZ(0,math.pi/4.5,0) --The amount of flips. 1 = -16, 2 = -8
        wait()
      end
      for i=1, 5 do --The amount of time your guy flips.
        Gyro.cframe = Gyro.cframe*CFrame.fromEulerAnglesXYZ(math.pi/-5,0,0) --The amount of flips. 1 = -16, 2 = -8
        wait()
      end
      Gyro.cframe = CF
      wait()
      Gyro:Remove()
      if not useps then
          togglestates(true)
      else
         hum.PlatformStand = false
      end
      _restoreproperties()
      debounce=false
    end
    t.Activated:Connect(Flip)
    local function tt()
        t.ToolTip = t.Parent == chr and "Flip flip flip!" or "Makes ya do a 360 flip :3"
    end
    t.Equipped:Connect(tt)
    t.Unequipped:Connect(tt)
  end
})

local npcs = {}
addcmd("flingnpcs",{
  addtoname = "/flinghumanoids",
  desc = "flings npcs as you get ownership of them",
  aliases = {"flinghumanoids"},
  func = function(args,speaker)
    unbind("NPCFling")
    local function disappear(hum)
      if hum:IsA("Humanoid") and not Players:GetPlayerFromCharacter(hum.Parent) then
        table.insert(npcs,{hum,hum.HipHeight})
        hum.HipHeight = 1024 --1024 is the max roblox allows
      end
    end
    for _,hum in pairs(workspace:GetDescendants()) do
      disappear(hum)
    end
    bind("NPCFling",workspace.DescendantAdded,disappear)
    notify("NPCs are now being flung")
  end
})

addcmd("unflingnpcs",{
  addtoname = "/unflinghumanoids",
  desc = "stops flinging npcs",
  aliases = {"unflinghumanoids"},
  func = function(args,speaker)
    unbind("NPCFling")
    for _,hum in pairs(npcs) do
        hum[1].HipHeight = hum[2]
    end
    npcs = {}
    notify("NPCs are no longer being flung")
  end
})

--removed due to results being inconsistent, code left in for anyone to try, dm Knux#9449 if you get them to enable consistently
--[[local disabledtouchinterests = {}
addcmd("notouchinterests",{
  addtoname = "/disabletouchinterests",
  desc = "disables TouchInterests from working",
  aliases = {"disabletouchinterests"},
  func = function(args,speaker)
    unbind("NoTI")
    local function disabletouch(TI,e)
      if TI:IsA("TouchTransmitter") then
        if not e then rinfo(TI.Parent) end
        table.insert(disabledtouchinterests,TI.Parent)
        TI:Destroy()
      end
    end
    for _,ti in pairs(workspace:GetDescendants()) do
        disabletouch(ti,true)
    end
    bind("NoTI",workspace.DescendantAdded,disabletouch)
    notify("TouchInterests are now disabled")
  end
})

addcmd("enabletouchinterests",{
  desc = "enables TouchInterests again",
  func = function(args,speaker)
    unbind("NoTI")
    function enabletouch(part)
      part.Touched:Connect(function() end)
    end
    for _,part in pairs(disabledtouchinterests) do
      enabletouch(part)
    end
    disabledtouchinterests = {}
    notify("TouchInterests are now enabled")
  end
})]]

addcmd("backupsave",{
  desc = "backs up your savefile in case it gets corrupted",
  func = function()
    notify("Please wait")
    local save = readfile("IY_FE.iy")
    local n,i = "IY_FE_Backup%s",1
    local name = n:format(".iy")
    while isfile(name) do
      name = n:format(" ("..i..").iy")
      i+=1
    end
    writefile(name,save)
    notify("Saved to "..name)
  end
})

local isauto = readsave("AutoBackupsEnabled")
if isauto then
  local save = readfile("IY_FE.iy")
  writefile("IY_FE_AutoBackup.iy",save)
end
addcmd("autobackup",{
  addtoname = "/autobackupsave",
  desc = "automatically backs up your save file",
  aliases = {"autobackupsave"},
  func = function()
    local isauto = readsave("AutoBackupsEnabled")
    if not isauto then
      writesave("AutoBackupsEnabled",true)
      local save = readfile("IY_FE.iy")
      writefile("IY_FE_AutoBackup.iy",save)
    end
    notify("Automatic save backups are now enabled")
  end
})

addcmd("noautobackup",{
  addtoname = "/noautobackupsave",
  desc = "stops automatically backing up your save file",
  aliases = {"noautobackupsave"},
  func = function()
    local isauto = readsave("AutoBackupsEnabled")
    if isauto then
      writesave("AutoBackupsEnabled",false)
    end
    notify("Automatic save backups are now disabled")
  end
})

return betteriy
