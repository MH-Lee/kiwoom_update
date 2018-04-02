from update import UpdateGobble

u = UpdateGobble()

u.step_one_kiwoom()
try:
    u.make_folder()
except FileExistsError:
    pass
u.set_tasks()
u.req_buysell()
u.req_short()
