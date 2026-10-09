import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from botc_deck.__main__ import BotCApp
from botc_deck.pages.main import MainPage
from botc_deck.pages.bluetooth import BluetoothPage
from botc_deck.pages.system import SystemPage

async def test_all():
    print("Testing BotCApp initialization...")
    app = BotCApp()

    print("Testing MainPage rendering (Day mode)...")
    app.state.active_mode = "day"
    main_p = MainPage(app)
    for k in range(15):
        img = await main_p.get_image(k)
        assert img.size == (72, 72)
    assert not app.renderer.is_night
    print("MainPage (Day): 15 buttons rendered ok.")

    print("Testing MainPage rendering (Night mode)...")
    app.state.active_mode = "night"
    for k in range(15):
        img = await main_p.get_image(k)
        assert img.size == (72, 72)
    assert app.renderer.is_night
    print("MainPage (Night): 15 buttons rendered in red theme ok.")


    print("Testing BluetoothPage rendering...")
    bt_p = BluetoothPage(app)
    for k in range(15):
        img = await bt_p.get_image(k)
        assert img.size == (72, 72)
    print("BluetoothPage: 15 buttons rendered ok.")

    print("Testing SystemPage rendering...")
    sys_p = SystemPage(app)
    for k in range(15):
        img = await sys_p.get_image(k)
        assert img.size == (72, 72)
    print("SystemPage: 15 buttons rendered ok.")

    print("Testing Timer Logic...")
    app.timers.start_timer(1)
    assert app.timers.is_running
    assert app.timers.active_minutes == 1
    rem_str = app.timers.get_remaining_str()
    print(f"Timer remaining format: {rem_str}")
    assert rem_str in ("01:00", "00:59")
    await app.timers.cancel_timer(trigger_bell=False)
    assert not app.timers.is_running
    print("Timer cancelled ok.")

    print("Testing State Save / Restore...")
    app.state.day_position = 123.4
    app.state.save()
    app.state.load()
    assert abs(app.state.day_position - 123.4) < 0.01
    print("State persistence ok.")

    print("All simulation tests passed successfully!")

if __name__ == "__main__":
    from botc_deck.__main__ import BotCApp
    asyncio.run(test_all())
