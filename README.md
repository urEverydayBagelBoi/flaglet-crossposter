# What is this?
This is a crossposting social bot, written in Python. I develop it primarily for a social, online art collective/group I'm working on.
Messages containing a configured tag (`!art` by default) will be crossposted by the bot to a feed channel. That's it.

## Details
- Assumes being run and configured for a **single server**. Not as an app.
- Narrow-scoped

# Contributing and Dev Guidelines
Mostly notes for myself since I'm not really expecting an influx of contributions xP

- Keep functionality narrowed to crossposting messages and connecting various platforms
- Keep things platform-agnostic wherever possible.
- Try to modularize things wherever possible, especially relating to platform support
- Since I'm a very amateur programmer, suggestions for how things could be entirely different are welcome and appreciated
- Please don't just sloperate (LLM-generate) half-hallucinated PR's together if you're not testing and inspecting them yourself. I'm trying to learn and experiment here. I could prompt an LLM myself, thanks.

# Road map
- [x] Basic functionality
- [ ] Support for stoat.chat (also other platforms later)
- [ ] Send crossposts into a moderator channel to be approved, before being posted across all platforms
- [ ] Send crossposts as a fancy embed, consistent across all platforms
- [ ] Persistently connect posts somehow (I.E. so that a post may be deleted along with equivalent crossposts across all platforms)