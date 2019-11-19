# В чем суть:
# Пользователь принадлежит одной из ролей. Роли могут быть доступны виртуалки следующим образом:
# Если это self-service role, то только те виртуальные машины, где этот юзер прописан в owner или grantedtolist.
# Если это Delegated Admin - то ему доступны некие хост-группы и облака, следовательно порядок следующий:
# Все машины конкретной хост группы, все машины конкретного облака, все машины с этим персонажем в owner, все машины с этим персонажем в grantedtolist
# Если администратор - то просто все машины.

$domain = $args[0]
$username = $args[1]
$name = $domain + "\" + $username

$user_roles = @()
$VMs = @()

# Есть хоть одна роль с общей админкой
$admin_flag = $false

# Есть хотя бы одна роль с Delegated Admin
$deleg_flag = $false

# Узнаем, есть ли общая админка у человека и список delegated admin ролей
$tmp = @(Get-SCUserRoleMembership -UserName $name | Select-Object Name, UserRoleProfile)
foreach ($role in $tmp)
{
    if ($role.UserRoleProfile -eq "Administrator") {
        $admin_flag = $true
    } elseif ($role.UserRoleProfile -eq "DelegatedAdmin") {
        $deleg_flag = $true
        $user_roles += $role.Name
    }
}

# Если есть роль глобального администратора - возвращаем список всех виртуальных машин, т.к. он со всеми может взаимодействовать
if ($admin_flag) {
    $VMs = @(Get-SCVirtualMachine |`
    Where-Object VMHost -ne $null |`
    Select-Object Name, VMID, VirtualMachineState, MostRecentTask, MostRecentTaskUIState, VMHost)
} else {
    # Иначе - проверяем наличие delegated admin ролей, на каждую такую роль запрашиваем список доступных виртуалок
    if ($deleg_flag) {
        foreach ($role in $user_roles) {
            $hostgroups = @((Get-SCUserRole -Name $role).HostGroup)
            $clouds = @((Get-SCUserRole -Name $role).Cloud)

            # Добавляем машины из хостов
            foreach ($hostgroup in $hostgroups) {
                $hosts = @()
                foreach ($x in $hostgroup.Hosts) {
                    $hosts += $x.Name
                }

                $tmp = Get-SCVirtualMachine |`
                 Where-Object VMHost -In $hosts
                foreach ($vm in $tmp) {
                    $VMs += $vm
                }
            }

            # Добавляем машины из облака
            foreach ($cloud in $clouds) {
                $tmp = Get-SCVirtualMachine -Cloud $cloud

                 foreach ($vm in $tmp) {
                     $VMs += $vm
                 }
            }
        }
    }

    # Добавляем выданные лично пользователю виртуалки
    $tmp = Get-SCVirtualMachine |`
    Where-Object { $_.GrantedToList.User -eq $name -or $_.Owner -eq $name }

    foreach ($vm in $tmp) {
        $VMs += $vm
    }

    # Убираем дубликаты
    $VMs = $VMs | Where-Object VMHost -ne $null | Select-Object -Unique | Select-Object Name, VMID, VirtualMachineState, MostRecentTask, MostRecentTaskUIState, VMHost
}

function IsNullOrWhitespace($str) {
    if ([string]::IsNullOrWhitespace($str)) {
        return "-"
    } else {
        return $str.ToString()
    }
}

$VMs | ForEach-Object {
    New-Object -Type PSObject -Property @{
        'Name' = IsNullOrWhitespace($_.Name)
        'VMId' = IsNullOrWhitespace($_.VMId)
        'VirtualMachineState' = IsNullOrWhitespace($_.VirtualMachineState)
        'MostRecentTask' = IsNullOrWhitespace($_.MostRecentTask)
        'MostRecentTaskUIState' = IsNullOrWhitespace($_.MostRecentTaskUIState)
        'VMHost' = IsNullOrWhitespace($_.VMHost)
        }
    }