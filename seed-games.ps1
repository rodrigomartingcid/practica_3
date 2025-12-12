# Rellena/actualiza juegos.
# Ejecutar con el backend levantado en http://127.0.0.1:5000

$ApiBase = 'http://127.0.0.1:5000/api'

# === Catálogo ===
$Games = @(
    @{ name='EA FC 26';                 genre='Deportes';          url='https://www.ea.com/games/ea-sports-fc';                                                  image_url='/assets/covers/ea_fc.jpg' }
    @{ name='Fortnite';                 genre='Battle Royale';     url='https://www.fortnite.com';                                                                image_url='/assets/covers/fortnite.jpg' }
    @{ name='NBA 2K26';                 genre='Deportes';          url='https://nba.2k.com/';                                                                     image_url='/assets/covers/NBA.jpg' }
    @{ name='Call of Duty: Black Ops 7';genre='FPS';               url='https://www.callofduty.com/';                                                            image_url='/assets/covers/bo7.jpg' }
    @{ name='Elden Ring';               genre='RPG';               url='https://en.bandainamcoent.eu/elden-ring/elden-ring';                                     image_url='/assets/covers/elder.jpg' }
    @{ name='Zelda: Tears of the Kingdom'; genre='Aventura';       url='https://www.nintendo.com/es-es/Juegos/Juegos-de-Nintendo-Switch/The-Legend-of-Zelda-Breath-of-the-Wild-1173609.html'; image_url='/assets/covers/zelda.jpg' }
    @{ name='Minecraft';                genre='Sandbox';           url='https://www.minecraft.net/';                                                              image_url='/assets/covers/minecraft.jpg' }
    @{ name='Cyberpunk 2077';           genre='RPG';               url='https://www.cyberpunk.net/';                                                              image_url='/assets/covers/cyberpunk.jpg' }
    @{ name='Rocket League';            genre='Deportes';          url='https://www.rocketleague.com/';                                                           image_url='/assets/covers/rocket.jpg' }
    @{ name='GTA V';                    genre='Acción';            url='https://www.rockstargames.com/gta-v';                                                     image_url='/assets/covers/gta.jpg' }
    @{ name='Red Dead Redemption 2';    genre='Acción/Aventura';   url='https://www.rockstargames.com/reddeadredemption2';                                       image_url='/assets/covers/reddead.jpg' }
    @{ name='Super Mario Bros Wonder';  genre='Plataformas';       url='https://www.nintendo.com/games/detail/super-mario-bros-wonder-switch/';                  image_url='/assets/covers/mariobros.jpg' }
    @{ name='Forza Horizon 5';          genre='Carreras';          url='https://forza.net/horizon';                                                               image_url='/assets/covers/forzahorizon.jpg' }
    @{ name='Gran Turismo 7';           genre='Simulación';        url='https://www.gran-turismo.com/';                                                           image_url='/assets/covers/granturismo.jpg' }
    @{ name="Assassin's Creed Shadows"; genre='Acción/Aventura';   url='https://www.ubisoft.com/es-es/game/assassins-creed/shadows';                             image_url='/assets/covers/assasinscreed.jpg' }
)

# === Helpers ===
function Get-AllGamesMap {
    try {
        $uri = $ApiBase + '/games?limit=500&offset=0'
        $resp = Invoke-RestMethod -Uri $uri -Method GET
        $map = @{}
        if ($resp -and $resp.items) {
            foreach ($g in $resp.items) {
                if ($null -ne $g.name) { $map[$g.name] = $g }
            }
        }
        return $map
    } catch {
        Write-Error ('No se pudo listar juegos: ' + $_.Exception.Message)
        return @{}
    }
}

function Upsert-Game {
    param(
        [Parameter(Mandatory=$true)] $game,
        [Parameter(Mandatory=$true)] $existingMap
    )

    $name = $game.name
    $bodyObj = @{
        name      = $game.name
        genre     = $game.genre
        url       = $game.url
        image_url = $game.image_url
    }
    $body = $bodyObj | ConvertTo-Json -Depth 4

    if ($existingMap.ContainsKey($name)) {
        $id = $existingMap[$name].id
        try {
            $uri = $ApiBase + '/games/' + $id
            $r = Invoke-RestMethod -Uri $uri -Method PATCH -Headers @{ 'Content-Type'='application/json' } -Body $body
            Write-Host ('✓ PATCH ' + $name + '  (id=' + $id + ')')
            return $true
        } catch {
            Write-Warning ('✗ PATCH ' + $name + '  (id=' + $id + ') -> ' + $_.Exception.Message)
            return $false
        }
    } else {
        try {
            $uri = $ApiBase + '/games'
            $r = Invoke-RestMethod -Uri $uri -Method POST -Headers @{ 'Content-Type'='application/json' } -Body $body
            Write-Host ('＋ POST  ' + $name + '  (id=' + $r.id + ')')
            return $true
        } catch {
            Write-Warning ('✗ POST  ' + $name + ' -> ' + $_.Exception.Message)
            return $false
        }
    }
}

# === Ejecución ===
Write-Host ('Consultando juegos existentes en ' + $ApiBase + ' ...') -ForegroundColor Cyan
$existing = Get-AllGamesMap

$ok = 0; $fail = 0
foreach ($g in $Games) {
    if (Upsert-Game -game $g -existingMap $existing) { $ok++ } else { $fail++ }
}

Write-Host ''
Write-Host 'Resumen:' -ForegroundColor Cyan
Write-Host ('  Correctos: ' + $ok)
Write-Host ('  Fallidos : ' + $fail)

# Listado de verificación
try {
    $uri = $ApiBase + '/games?limit=50&offset=0'
    $resp = Invoke-RestMethod -Uri $uri -Method GET
    Write-Host "`nEjemplo de items devueltos:" -ForegroundColor Cyan
    $resp.items | Select-Object id,name,genre,image_url | Format-Table -AutoSize
} catch {
    Write-Warning ('No se pudo listar juegos al final: ' + $_.Exception.Message)
}
