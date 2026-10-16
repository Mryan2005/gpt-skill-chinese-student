# Confirm and reset

Show the impact report and wait for an explicit confirmation. After confirmation, set the manifest to CONFIRMED and run reset_derived_state.py --apply. Verify that every delete path is absent or recreated empty and every preserve path remains readable. Do not accept confirmation inferred from an earlier message.
