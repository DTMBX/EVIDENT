# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e2]:
    - generic [ref=e4]:
      - heading "BarberX" [level=1] [ref=e5]
      - paragraph [ref=e6]: A Cut Above
    - generic [ref=e7]:
      - generic [ref=e8]:
        - generic [ref=e9]: Email Address
        - generic [ref=e10]:
          - textbox "Email Address" [active] [ref=e11]:
            - /placeholder: your@email.com
          - img
      - generic [ref=e12]:
        - generic [ref=e13]: Password
        - generic [ref=e14]:
          - textbox "Password" [ref=e15]:
            - /placeholder: ••••••••
          - img
          - button "Toggle password visibility" [ref=e16] [cursor=pointer]:
            - img [ref=e17]
      - link "Forgot password?" [ref=e21] [cursor=pointer]:
        - /url: /auth/forgot-password
      - generic [ref=e22]:
        - checkbox "Remember me" [ref=e23] [cursor=pointer]
        - generic [ref=e24]: Remember me
      - button "Login" [ref=e25] [cursor=pointer]
    - generic [ref=e26]: OR
    - generic [ref=e27]:
      - text: Don't have an account?
      - link "Sign up now" [ref=e28] [cursor=pointer]:
        - /url: /auth/signup
    - link "Didn't receive verification email?" [ref=e30] [cursor=pointer]:
      - /url: "#"
  - status
```