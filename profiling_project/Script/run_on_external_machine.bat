for %%f in (*.exe) do %%f -stdout -utf8output -Messaging -SessionName="NameThatWillBeShownInFrontend" -execcmds="session AUTH username_of_controlling_pc"
pause